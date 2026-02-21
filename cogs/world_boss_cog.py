import discord
from discord.ext import commands
from database.connection import db
import asyncio
import random
from datetime import datetime
from utils.banner_manager import BannerManager

class WorldBossCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_hp_visuals(self, current, max_hp):
        """Generates the 3-Phase colored health bar."""
        perc = (current / max_hp) * 100
        filled = max(0, min(10, int(perc / 10)))
        
        if perc > 65: bar, color, label = "🟩" * filled, 0x00FF00, "PHASE 1: INITIAL"
        elif perc > 30: bar, color, label = "🟧" * filled, 0xFFA500, "PHASE 2: ENRAGED"
        else: bar, color, label = "🟥" * filled, 0xFF0000, "PHASE 3: UNLEASHED"
        
        return f"{bar}{'⬛' * (10-filled)} `{perc:.1f}%`", color, label

    async def execute_attack(self, ctx, category, move_num):
        """Player Attack: Stats + Skill Damage with CE Cost Check."""
        user_id = str(ctx.author.id)
        player = await db.players.find_one({"_id": user_id})
        boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})

        if not player: return await ctx.send("❌ Create a profile first!")
        if not boss: return await ctx.send("🌑 No active World Boss.")

        # 1. CE COST CHECK (Only for !CE commands)
        if category == "CE":
            ce_cost = move_num * 15 # Example: !CE 5 costs 75 CE
            current_ce = player.get("stats", {}).get("current_ce", 0)
            if current_ce < ce_cost:
                return await ctx.send(f"⚠️ Not enough Cursed Energy! (Need {ce_cost})")
            # Deduct CE
            await db.players.update_one({"_id": user_id}, {"$inc": {"stats.current_ce": -ce_cost}})

        # 2. DAMAGE CALCULATION
        skill_key = f"{category}{move_num}"
        skill_data = await db.skills.find_one({"skill_id": skill_key})
        skill_dmg = skill_data.get("damage", 0) if skill_data else 0
        player_dmg = player.get("stats", {}).get("dmg", 10)
        
        total_dmg = player_dmg + skill_dmg

        # 3. UPDATE DB & UI
        new_hp = max(0, boss["current_hp"] - total_dmg)
        await db.npcs.update_one({"_id": boss["_id"]}, {"$set": {"current_hp": new_hp}})
        
        hp_bar, color, label = self.get_hp_visuals(new_hp, boss["max_hp"])
        embed = discord.Embed(
            title=f"⚔️ ATTACK: {boss['name']}",
            description=f"**{ctx.author.name}** used **{skill_key}** dealing `{total_dmg:,}` damage!",
            color=color
        )
        embed.add_field(name="Boss Health", value=hp_bar, inline=False)
        BannerManager.apply(embed, type="combat")
        await ctx.send(embed=embed)

    # --- PREFIX COMMANDS ---
    @commands.command(name="CE")
    async def ce_cmd(self, ctx, m: int = 1): await self.execute_attack(ctx, "CE", m)
    @commands.command(name="F")
    async def f_cmd(self, ctx, m: int = 1): await self.execute_attack(ctx, "F", m)
    @commands.command(name="W")
    async def w_cmd(self, ctx, m: int = 1): await self.execute_attack(ctx, "W", m)

    # --- BOSS AOE LOOP ---
    async def world_boss_attack_loop(self, channel, boss_name):
        """The Boss uses its registered skills to attack everyone."""
        while True:
            boss = await db.npcs.find_one({"name": boss_name})
            if not boss or boss.get("current_hp", 0) <= 0:
                break

            # 1. SELECT RANDOM BOSS SKILL
            # Pulls from the !wb_skills data you set
            skills = [boss.get("technique"), boss.get("weapon"), boss.get("fighting_style")]
            active_skill = random.choice([s for s in skills if s]) or "Cursed Strike"

            # 2. CALCULATE AOE DAMAGE
            perc = (boss['current_hp'] / boss['max_hp']) * 100
            mult = 1.3 if perc > 65 else 2.6 if perc > 30 else 3.9
            final_dmg = int(boss.get("base_dmg", 100) * mult)

            hp_bar, color, label = self.get_hp_visuals(boss['current_hp'], boss['max_hp'])

            embed = discord.Embed(
                title=f"🚨 {boss_name} ACTIVATES {active_skill.upper()}",
                description=f"**{label}**\nThe boss unleashes a devastating move on everyone for `{final_dmg:,}` damage!",
                color=color
            )
            if "image" in boss: embed.set_thumbnail(url=boss["image"])
            BannerManager.apply(embed, type="combat")
            await channel.send(embed=embed)

            # 3. APPLY DAMAGE TO ALL TARGETS
            await db.players.update_many(
                {"stats.current_hp": {"$gt": 0}},
                {"$inc": {"stats.current_hp": -final_dmg}}
            )
            await asyncio.sleep(20)

async def setup(bot):
    await bot.add_cog(WorldBossCog(bot))
    
