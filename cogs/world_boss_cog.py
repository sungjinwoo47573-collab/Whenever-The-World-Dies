import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
import asyncio
import random
from datetime import datetime, timedelta

class WorldBossCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rarities = {
            "Common": "⚪", "Rare": "🔵", "Epic": "🟣", 
            "Legendary": "🟡", "Special Grade": "🔴"
        }
        # Local cache for cooldowns to reduce DB calls during fast combat
        self.cooldowns = {} 

    def get_hp_visuals(self, current, max_hp, phase=1):
        if max_hp <= 0: return "`[⬛⬛⬛⬛⬛]`", 0x000000, "DEAD"
        perc = (current / max_hp) * 100
        filled = max(0, min(10, int(perc / 10)))
        bar_emoji = "🟩" if phase == 1 else "🟥"
        return f"`{bar_emoji * filled}{'⬛' * (10-filled)}` **{perc:.1f}%**", 0, "LIVE"

    def calculate_black_flash(self, damage):
        if random.random() < 0.01: # 1% Chance
            return int(damage * 2.5), True
        return int(damage), False

    # --- ADMIN COMMANDS ---

    @app_commands.command(name="wb_cooldown", description="Admin: Set cooldowns for a skill set.")
    @app_commands.describe(name="Item name", m1="CD for Move 1", m2="CD for Move 2", m3="CD for Move 3", m4="CD for Move 4")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_cooldown(self, interaction: discord.Interaction, name: str, m1: int, m2: int, m3: int, m4: int):
        cds = [m1, m2, m3, m4]
        for i, cd in enumerate(cds, 1):
            await db.skills.update_one({"name": name, "move_number": i}, {"$set": {"cooldown": cd}})
        
        embed = discord.Embed(title="⏳ COOLDOWN REGISTRY", description=f"Updated: **{name}**", color=0x34495e)
        for i, cd in enumerate(cds, 1):
            embed.add_field(name=f"Move {i}", value=f"`{cd}s`", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="wb_start")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_start(self, interaction: discord.Interaction, boss_name: str):
        npc = await db.npcs.find_one({"name": boss_name, "is_world_boss": True})
        if not npc: return await interaction.response.send_message("❌ Boss not found.")
        await db.npcs.update_one({"_id": npc["_id"]}, {"$set": {"current_hp": npc["max_hp"], "phase": 1}})
        await interaction.response.send_message(f"🚨 **{npc['name']}** has manifested!")

    # --- DEATH LOCKOUT LOGIC ---

    async def handle_player_death(self, ctx, member: discord.Member):
        """Prevents the player from chatting in the raid channel for 10 seconds."""
        try:
            await ctx.channel.set_permissions(member, send_messages=False)
            await ctx.send(f"💀 **{member.mention} has lost consciousness!** (10s Lockout)")
            
            await asyncio.sleep(10)
            
            await ctx.channel.set_permissions(member, overwrite=None)
            # Restore a bit of HP so they can re-enter
            await db.players.update_one({"_id": str(member.id)}, {"$set": {"stats.current_hp": 50}})
            await ctx.send(f"❤️ **{member.mention}** has regained focus.", delete_after=5)
        except Exception as e:
            print(f"Permission Error: {e}")

    # --- COMBAT FLOW ---

    async def boss_retaliation(self, ctx, boss, target: discord.Member):
        phase_mult = 2.5 if boss.get("phase", 1) == 2 else 1.0
        dmg = int(boss.get("base_dmg", 100) * phase_mult * random.uniform(0.95, 1.05))
        
        quotes = boss.get("custom_dialogue") or ["“Know your place.”", "“Stand proud.”"]
        quote = random.choice(quotes)
        
        # Damage the specific attacker
        await db.players.update_one({"_id": str(target.id)}, {"$inc": {"stats.current_hp": -dmg}})
        p_data = await db.players.find_one({"_id": str(target.id)})

        hp_bar, _, _ = self.get_hp_visuals(boss['current_hp'], boss['max_hp'], phase=boss.get("phase", 1))
        
        await ctx.send(f"**{boss['name']}**: {quote}\n↳ *Deals `{dmg:,}` DMG to {target.mention}!*\n{hp_bar}")

        if p_data.get("stats", {}).get("current_hp", 0) <= 0:
            await self.handle_player_death(ctx, target)

    async def execute_attack(self, ctx, category, move_num):
        user_id = str(ctx.author.id)
        player = await db.players.find_one({"_id": user_id})
        boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})

        if not player or not boss: return

        # Check for active lockout (if permission sync fails)
        if player.get("stats", {}).get("current_hp", 0) <= 0:
            return await ctx.send(f"❌ {ctx.author.mention}, you are too exhausted to fight!", delete_after=3)

        loadout_key = {"CE": "technique", "W": "weapon", "F": "fighting_style"}[category]
        item_name = player.get("loadout", {}).get(loadout_key)
        skill = await db.skills.find_one({"name": item_name, "move_number": move_num})

        if not skill: return await ctx.send("❌ Skill not found.")

        # 1. COOLDOWN CHECK
        cd_key = f"{user_id}_{item_name}_{move_num}"
        now = datetime.utcnow()
        if cd_key in self.cooldowns:
            if now < self.cooldowns[cd_key]:
                retry_in = (self.cooldowns[cd_key] - now).total_seconds()
                return await ctx.send(f"⏳ **{skill['move_title']}** is on cooldown! (`{retry_in:.1f}s`)", delete_after=3)

        # 2. CE COST
        if category == "CE":
            cost = move_num * 15
            if player['stats']['current_ce'] < cost:
                return await ctx.send(f"⚠️ Insufficient CE! (`{player['stats']['current_ce']}/{cost}`)")
            await db.players.update_one({"_id": user_id}, {"$inc": {"stats.current_ce": -cost}})

        # 3. APPLY COOLDOWN
        cd_seconds = skill.get("cooldown", 2)
        self.cooldowns[cd_key] = now + timedelta(seconds=cd_seconds)

        # 4. DAMAGE LOGIC
        dmg_calc = (player['stats']['dmg'] + skill.get("damage", 0)) * random.uniform(0.98, 1.05)
        final_dmg, is_bf = self.calculate_black_flash(dmg_calc)
        
        new_hp = max(0, boss['current_hp'] - final_dmg)
        await db.npcs.update_one({"_id": boss["_id"]}, {"$set": {"current_hp": new_hp}})

        emoji = self.rarities.get(skill.get("rarity", "Common"), "⚪")
        bf_text = "✨ **BLACK FLASH!** " if is_bf else ""
        await ctx.send(f"⚔️ {bf_text}**{ctx.author.name}** uses {emoji} **{skill['move_title']}**! (`-{int(final_dmg):,}` HP)")

        if new_hp > 0:
            await asyncio.sleep(1.2)
            boss['current_hp'] = new_hp
            await self.boss_retaliation(ctx, boss, ctx.author)
        else:
            await ctx.send(f"🎊 **{boss['name']} has been defeated!**")

    @commands.command(name="CE")
    async def ce(self, ctx, m: int = 1): await self.execute_attack(ctx, "CE", m)
    @commands.command(name="W")
    async def w(self, ctx, m: int = 1): await self.execute_attack(ctx, "W", m)
    @commands.command(name="F")
    async def f(self, ctx, m: int = 1): await self.execute_attack(ctx, "F", m)

async def setup(bot):
    await bot.add_cog(WorldBossCog(bot))
    
