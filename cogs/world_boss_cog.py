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
        self.revenge_meter = {} # Tracks KOs for guaranteed Black Flash

    def get_hp_visuals(self, current, max_hp, phase=1):
        if max_hp <= 0: return "`[⬛⬛⬛⬛⬛]`", 0x000000, "DEAD"
        perc = (current / max_hp) * 100
        filled = max(0, min(10, int(perc / 10)))
        bar_emoji = "🟩" if phase == 1 else "🟥"
        return f"`{bar_emoji * filled}{'⬛' * (10-filled)}` **{perc:.1f}%**", 0, "LIVE"

    # --- STATUS COMMAND ---

    @app_commands.command(name="status", description="Check your vitals and the current World Boss status.")
    async def status(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})
        boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})

        embed = discord.Embed(title="📊 BATTLEFIELD STATUS", color=0x2b2d31)

        # Player Section
        hp = player['stats']['current_hp']
        ce = player['stats']['current_ce']
        rev = self.revenge_meter.get(user_id, 0)
        rev_status = "🔥 READY" if rev >= 3 else f"{rev}/3"
        
        embed.add_field(
            name=f"👤 {interaction.user.name}",
            value=f"**HP:** `{hp}`\n**CE:** `{ce}`\n**Revenge:** `{rev_status}`",
            inline=True
        )

        # Boss Section
        if boss:
            hp_bar, _, label = self.get_hp_visuals(boss['current_hp'], boss['max_hp'], boss.get('phase', 1))
            embed.add_field(
                name=f"👺 {boss['name']} ({label})",
                value=f"{hp_bar}\n**Level:** `Special Grade`",
                inline=True
            )
        else:
            embed.add_field(name="👺 Boss", value="*No active threat detected.*", inline=True)

        await interaction.response.send_message(embed=embed)

    # --- UPDATED DEATH LOGIC ---

    async def handle_player_death(self, ctx, member: discord.Member):
        user_id = str(member.id)
        # Increase Revenge Meter on death
        self.revenge_meter[user_id] = self.revenge_meter.get(user_id, 0) + 1
        
        await ctx.channel.set_permissions(member, send_messages=False)
        await ctx.send(f"💀 **{member.mention} has lost consciousness!** (10s Lockout)\n*Revenge Meter: {self.revenge_meter[user_id]}/3*")
        
        await asyncio.sleep(10)
        
        await ctx.channel.set_permissions(member, overwrite=None)
        await db.players.update_one({"_id": user_id}, {"$set": {"stats.current_hp": 100}})
        await ctx.send(f"❤️ **{member.mention}** has returned to the fray.", delete_after=5)

    # --- UPDATED ATTACK LOGIC ---

    async def execute_attack(self, ctx, category, move_num):
        user_id = str(ctx.author.id)
        player = await db.players.find_one({"_id": user_id})
        boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})

        if not player or not boss: return
        if player['stats']['current_hp'] <= 0:
            return await ctx.send("❌ You are incapacitated!", delete_after=3)

        loadout_key = {"CE": "technique", "W": "weapon", "F": "fighting_style"}[category]
        item_name = player.get("loadout", {}).get(loadout_key)
        skill = await db.skills.find_one({"name": item_name, "move_number": move_num})

        if not skill: return await ctx.send("❌ Skill not found.")

        # Cooldown check
        cd_key = f"{user_id}_{item_name}_{move_num}"
        now = datetime.utcnow()
        if cd_key in self.cooldowns and now < self.cooldowns[cd_key]:
            return await ctx.send(f"⏳ **{skill['move_title']}** is on cooldown!", delete_after=2)

        # CE Check
        if category == "CE":
            cost = move_num * 15
            if player['stats']['current_ce'] < cost:
                return await ctx.send(f"⚠️ Insufficient CE!")
            await db.players.update_one({"_id": user_id}, {"$inc": {"stats.current_ce": -cost}})

        # Set Cooldown
        self.cooldowns[cd_key] = now + timedelta(seconds=skill.get("cooldown", 3))

        # Damage + Revenge Check
        dmg_calc = (player['stats']['dmg'] + skill.get("damage", 0)) * random.uniform(0.98, 1.05)
        
        # Guaranteed Black Flash if Revenge >= 3
        if self.revenge_meter.get(user_id, 0) >= 3:
            final_dmg, is_bf = int(dmg_calc * 2.5), True
            self.revenge_meter[user_id] = 0 # Reset meter
        else:
            final_dmg, is_bf = self.calculate_black_flash(dmg_calc)

        new_hp = max(0, boss['current_hp'] - final_dmg)
        await db.npcs.update_one({"_id": boss["_id"]}, {"$set": {"current_hp": new_hp}})

        bf_text = "✨ **BLACK FLASH!** " if is_bf else ""
        await ctx.send(f"⚔️ {bf_text}**{ctx.author.name}** uses **{skill['move_title']}**! (`-{int(final_dmg):,}` HP)")

        if new_hp > 0:
            await asyncio.sleep(1.2)
            boss['current_hp'] = new_hp
            await self.boss_retaliation(ctx, boss, ctx.author)
        else:
            await ctx.send(f"🎊 **{boss['name']} defeated!**")

    # --- [Remaining Methods: boss_retaliation, ce, w, f, setup...] ---
        
