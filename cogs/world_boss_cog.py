import discord
from discord.ext import commands
from database.connection import db
import asyncio
import random
from utils.banner_manager import BannerManager

class WorldBossCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_hp_visuals(self, current, max_hp, phase=1):
        perc = (current / max_hp) * 100
        filled = max(0, min(10, int(perc / 10)))
        # Visuals for Phase 1 vs Phase 2
        color = 0x00FF00 if phase == 1 else 0xFF0000
        label = "PHASE 1: MORTAL" if phase == 1 else "PHASE 2: ASCENDED"
        bar = ("🟩" if phase == 1 else "🟥") * filled
        return f"{bar}{'⬛' * (10-filled)} `{perc:.1f}%`", color, label

    async def execute_attack(self, ctx, category, move_num):
        player = await db.players.find_one({"_id": str(ctx.author.id)})
        boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})
        if not player or not boss: return await ctx.send("🌑 No active battle.")

        # 1. CE COST
        if category == "CE":
            cost = move_num * 15
            if player.get("stats", {}).get("current_ce", 0) < cost:
                return await ctx.send(f"⚠️ Need {cost} CE!")
            await db.players.update_one({"_id": str(ctx.author.id)}, {"$inc": {"stats.current_ce": -cost}})

        # 2. DAMAGE CALCULATION (Player Stats + Skill)
        skill_key = f"{category}{move_num}"
        skill_data = await db.skills.find_one({"skill_id": skill_key})
        total_dmg = player.get("stats", {}).get("dmg", 10) + (skill_data.get("damage", 0) if skill_data else 0)

        new_hp = max(0, boss["current_hp"] - total_dmg)
        await db.npcs.update_one({"_id": boss["_id"]}, {"$set": {"current_hp": new_hp}})
        
        hp_bar, color, label = self.get_hp_visuals(new_hp, boss["max_hp"], phase=boss.get("phase", 1))
        embed = discord.Embed(title=f"⚔️ {ctx.author.name} vs {boss['name']}", description=f"Dealt `{total_dmg:,}` damage!", color=color)
        embed.add_field(name=f"Status: {label}", value=hp_bar)
        BannerManager.apply(embed, type="combat")
        await ctx.send(embed=embed)

        # 3. DEATH / TRANSFORMATION LOGIC
        if new_hp <= 0:
            if boss.get("phase", 1) == 1:
                await self.trigger_phase_two(ctx, boss)
            else:
                await ctx.send(f"🎊 **{boss['name']} HAS BEEN FULLY EXORCISED!**")

    async def trigger_phase_two(self, ctx, boss):
        """Handles the 'fake' death and Phase 2 resurrection."""
        await ctx.send(f"⚠️ **{boss['name']}'s presence is changing... SOMETHING IS WRONG!**")
        await asyncio.sleep(3)
        
        # Phase 2 Stats: 2.5x HP and marked as Phase 2
        p2_hp = int(boss["max_hp"] * 2.5)
        await db.npcs.update_one(
            {"_id": boss["_id"]}, 
            {"$set": {"current_hp": p2_hp, "max_hp": p2_hp, "phase": 2}}
        )
        
        embed = discord.Embed(
            title=f"🔥 PHASE 2: {boss['name']} ASCENDED",
            description=f"The curse has evolved! Its power has multiplied by **2.5x**!",
            color=0xFF0000
        )
        BannerManager.apply(embed, type="combat")
        await ctx.send(embed=embed)

    async def boss_attack_loop(self, channel, boss_name):
        while True:
            boss = await db.npcs.find_one({"name": boss_name})
            if not boss or boss.get("current_hp", 0) <= 0: break
            
            # 1. Random 2-5% Buff/Debuff Variance
            variance = random.uniform(0.95, 1.05) # Random factor between 0.95 and 1.05
            
            # 2. Phase Multiplier
            # Phase 1: Normal | Phase 2: 2.5x Stats
            phase_mult = 2.5 if boss.get("phase", 1) == 2 else 1.0
            
            base_dmg = boss.get("base_dmg", 100)
            final_dmg = int(base_dmg * phase_mult * variance)

            # 3. UI and Damage
            skill = random.choice([boss.get("technique"), boss.get("weapon"), boss.get("fighting_style")]) or "Cursed Strike"
            hp_bar, color, label = self.get_hp_visuals(boss['current_hp'], boss['max_hp'], phase=boss.get("phase", 1))
            
            embed = discord.Embed(
                title=f"🚨 {boss_name} ACTIVATES {skill.upper()}",
                description=f"**{label}**\nDamage dealt: `{final_dmg:,}` (Variance: `{variance:.1%}`)",
                color=color
            )
            BannerManager.apply(embed, type="combat")
            await channel.send(embed=embed)
            
            await db.players.update_many({"stats.current_hp": {"$gt": 0}}, {"$inc": {"stats.current_hp": -final_dmg}})
            await asyncio.sleep(20)

async def setup(bot):
    await bot.add_cog(WorldBossCog(bot))
        
