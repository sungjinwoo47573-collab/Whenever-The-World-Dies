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
        self.rarities = {"Common": "⚪", "Rare": "🔵", "Epic": "🟣", "Legendary": "🟡", "Special Grade": "🔴"}
        self.cooldowns = {} 
        self.revenge_meter = {}
        self.aggro_list = set() # Tracks the 8 active raiders
        self.MAX_RAIDERS = 8

    def get_hp_visuals(self, current, max_hp, phase=1):
        if max_hp <= 0: return "`[⬛⬛⬛⬛⬛]`", 0x000000, "DEAD"
        perc = (current / max_hp) * 100
        filled = max(0, min(10, int(perc / 10)))
        bar_emoji = "🟩" if phase == 1 else "🟥"
        return f"`{bar_emoji * filled}{'⬛' * (10-filled)}` **{perc:.1f}%**", 0, "LIVE"

    def calculate_black_flash(self, damage):
        if random.random() < 0.01:
            return int(damage * 2.5), True
        return int(damage), False

    # --- STATUS COMMAND ---

    @app_commands.command(name="status", description="Check raid capacity and boss vitals.")
    async def status(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})
        boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})

        embed = discord.Embed(title="📊 RAID MONITOR", color=0x2b2d31)
        
        # Capacity Section
        cap_color = "🔴" if len(self.aggro_list) >= self.MAX_RAIDERS else "🟢"
        embed.add_field(
            name="🏰 Raid Capacity", 
            value=f"{cap_color} `{len(self.aggro_list)}/{self.MAX_RAIDERS}` Players Engaged", 
            inline=False
        )

        if boss:
            hp_bar, _, label = self.get_hp_visuals(boss['current_hp'], boss['max_hp'], boss.get('phase', 1))
            embed.add_field(name=f"👺 {boss['name']} ({label})", value=hp_bar, inline=True)
            
        if player:
            rev = self.revenge_meter.get(user_id, 0)
            embed.add_field(
                name=f"👤 {interaction.user.name}", 
                value=f"HP: `{player['stats']['current_hp']}`\nRevenge: `{rev}/3`", 
                inline=True
            )

        await interaction.response.send_message(embed=embed)

    # --- DEATH & LOCKOUT ---

    async def handle_player_death(self, ctx, member: discord.Member):
        user_id = str(member.id)
        if user_id in self.aggro_list:
            self.aggro_list.remove(user_id) # Free up a raid slot
        
        self.revenge_meter[user_id] = self.revenge_meter.get(user_id, 0) + 1
        
        try:
            await ctx.channel.set_permissions(member, send_messages=False)
            await ctx.send(f"💀 **{member.mention} has fallen!** A raid slot has opened up. (10s Lockout)")
            
            await asyncio.sleep(10)
            
            await ctx.channel.set_permissions(member, overwrite=None)
            await db.players.update_one({"_id": user_id}, {"$set": {"stats.current_hp": 100}})
            await ctx.send(f"❤️ **{member.mention}** has regained consciousness.", delete_after=5)
        except: pass

    # --- AOE RETALIATION ---

    async def boss_retaliation(self, ctx, boss):
        if not self.aggro_list: return

        phase_mult = 2.5 if boss.get("phase", 1) == 2 else 1.0
        quotes = boss.get("custom_dialogue") or ["“Know your place.”", "“You are all beneath me.”"]
        
        await ctx.send(f"**{boss['name']}**: {random.choice(quotes)}\n↳ *The boss unleashes an AOE strike!*")

        targets = list(self.aggro_list)
        for uid in targets:
            member = ctx.guild.get_member(int(uid))
            if not member: continue

            dmg = int(boss.get("base_dmg", 100) * phase_mult * random.uniform(0.9, 1.1))
            await db.players.update_one({"_id": uid}, {"$inc": {"stats.current_hp": -dmg}})
            
            p_data = await db.players.find_one({"_id": uid})
            if p_data.get("stats", {}).get("current_hp", 0) <= 0:
                self.bot.loop.create_task(self.handle_player_death(ctx, member))

        hp_bar, _, _ = self.get_hp_visuals(boss['current_hp'], boss['max_hp'], boss.get('phase', 1))
        await ctx.send(hp_bar)

    # --- ATTACK EXECUTION ---

    async def execute_attack(self, ctx, category, move_num):
        user_id = str(ctx.author.id)
        player = await db.players.find_one({"_id": user_id})
        boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})

        if not player or not boss: return

        # 1. RAID CAPACITY CHECK
        if user_id not in self.aggro_list:
            if len(self.aggro_list) >= self.MAX_RAIDERS:
                return await ctx.send(f"🚫 **Raid is Full!** ({self.MAX_RAIDERS}/{self.MAX_RAIDERS}) Wait for someone to fall!", delete_after=5)
            self.aggro_list.add(user_id)

        # 2. VITALS CHECK
        if player['stats']['current_hp'] <= 0:
            return await ctx.send("❌ You are unconscious!", delete_after=3)

        # 3. ITEM & COOLDOWN CHECK
        loadout_key = {"CE": "technique", "W": "weapon", "F": "fighting_style"}[category]
        item_name = player.get("loadout", {}).get(loadout_key)
        skill = await db.skills.find_one({"name": item_name, "move_number": move_num})
        if not skill: return await ctx.send("❌ Skill not found.")

        cd_key = f"{user_id}_{item_name}_{move_num}"
        now = datetime.utcnow()
        if cd_key in self.cooldowns and now < self.cooldowns[cd_key]:
            return await ctx.send("⏳ On cooldown!", delete_after=2)

        # 4. DAMAGE + REVENGE
        dmg_calc = (player['stats']['dmg'] + skill.get("damage", 0)) * random.uniform(0.98, 1.05)
        if self.revenge_meter.get(user_id, 0) >= 3:
            final_dmg, is_bf = int(dmg_calc * 2.5), True
            self.revenge_meter[user_id] = 0
        else:
            final_dmg, is_bf = self.calculate_black_flash(dmg_calc)

        # Update DB
        new_hp = max(0, boss['current_hp'] - final_dmg)
        await db.npcs.update_one({"_id": boss["_id"]}, {"$set": {"current_hp": new_hp}})
        self.cooldowns[cd_key] = now + timedelta(seconds=skill.get("cooldown", 3))

        # UI Output
        bf_text = "✨ **BLACK FLASH!** " if is_bf else ""
        await ctx.send(f"⚔️ {bf_text}**{ctx.author.name}** hits **{boss['name']}**! (`-{int(final_dmg):,}` HP)")

        if new_hp > 0:
            await asyncio.sleep(1.2)
            boss['current_hp'] = new_hp
            await self.boss_retaliation(ctx, boss)
        else:
            self.aggro_list.clear()
            await ctx.send(f"🎊 **{boss['name']} defeated!**")

    # --- PREFIX COMMANDS ---
    @commands.command(name="CE")
    async def ce(self, ctx, m: int = 1): await self.execute_attack(ctx, "CE", m)
    @commands.command(name="W")
    async def w(self, ctx, m: int = 1): await self.execute_attack(ctx, "W", m)
    @commands.command(name="F")
    async def f(self, ctx, m: int = 1): await self.execute_attack(ctx, "F", m)

async def setup(bot):
    await bot.add_cog(WorldBossCog(bot))
    
