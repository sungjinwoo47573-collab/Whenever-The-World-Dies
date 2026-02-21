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
        """Generates visual HP bar and phase info."""
        perc = (current / max_hp) * 100
        filled = max(0, min(10, int(perc / 10)))
        color = 0x00FF00 if phase == 1 else 0xFF0000
        label = "PHASE 1: MORTAL" if phase == 1 else "PHASE 2: ASCENDED"
        bar = ("🟩" if phase == 1 else "🟥") * filled
        return f"{bar}{'⬛' * (10-filled)} `{perc:.1f}%`", color, label

    async def boss_retaliation(self, ctx, boss):
        """The Boss only attacks back after being hit."""
        # 1. Random 2-5% Stats Buff/Debuff Variance
        variance = random.uniform(0.95, 1.05)
        
        # 2. Phase Multiplier (Phase 2 is 2.5x stronger)
        phase_mult = 2.5 if boss.get("phase", 1) == 2 else 1.0
        
        final_dmg = int(boss.get("base_dmg", 100) * phase_mult * variance)
        
        # 3. Select Skill
        skill = random.choice([boss.get("technique"), boss.get("weapon"), boss.get("fighting_style")]) or "Cursed Strike"
        
        hp_bar, color, label = self.get_hp_visuals(boss['current_hp'], boss['max_hp'], phase=boss.get("phase", 1))

        embed = discord.Embed(
            title=f"🚨 {boss['name']} COUNTERS!",
            description=f"**{boss['name']}** reacted to your strike with **{skill.upper()}**!\n"
                        f"💥 Damage dealt to you: `{final_dmg:,}`\n"
                        f"📊 Variance: `{variance:.1%}`",
            color=color
        )
        BannerManager.apply(embed, type="combat")
        await ctx.send(embed=embed)

        # Apply damage to the attacker
        await db.players.update_one(
            {"_id": str(ctx.author.id)},
            {"$inc": {"stats.current_hp": -final_dmg}}
        )

    async def execute_attack(self, ctx, category, move_num):
        """Main player attack logic."""
        player = await db.players.find_one({"_id": str(ctx.author.id)})
        boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})

        if not player or not boss: 
            return await ctx.send("🌑 There is no active boss to fight.")

        # 1. Handle Cursed Energy Cost
        if category == "CE":
            cost = move_num * 15
            if player.get("stats", {}).get("current_ce", 0) < cost:
                return await ctx.send(f"⚠️ Not enough CE! (Need {cost})")
            await db.players.update_one({"_id": str(ctx.author.id)}, {"$inc": {"stats.current_ce": -cost}})

        # 2. Player Damage (Stats + Skill)
        skill_key = f"{category}{move_num}"
        skill_data = await db.skills.find_one({"skill_id": skill_key})
        total_dmg = player.get("stats", {}).get("dmg", 10) + (skill_data.get("damage", 0) if skill_data else 0)

        new_hp = max(0, boss["current_hp"] - total_dmg)
        await db.npcs.update_one({"_id": boss["_id"]}, {"$set": {"current_hp": new_hp}})
        
        # Update local boss object for visual and check
        boss["current_hp"] = new_hp
        
        hp_bar, color, label = self.get_hp_visuals(new_hp, boss["max_hp"], phase=boss.get("phase", 1))
        
        player_embed = discord.Embed(
            title=f"⚔️ {ctx.author.name} attacks!",
            description=f"You used **{skill_key}** for `{total_dmg:,}` damage!\n\n**Boss HP:**\n{hp_bar}",
            color=color
        )
        BannerManager.apply(player_embed, type="combat")
        await ctx.send(embed=player_embed)

        # 3. Check for Phase 1 Death -> Phase 2 Transition
        if new_hp <= 0 and boss.get("phase", 1) == 1:
            await self.trigger_phase_two(ctx, boss)
        elif new_hp <= 0:
            await ctx.send(f"🎊 **{boss['name']} HAS BEEN FULLY EXORCISED!**")
        else:
            # 4. TRIGGER COUNTER-ATTACK (Reactive)
            await asyncio.sleep(1) # Small delay for immersion
            await self.boss_retaliation(ctx, boss)

    async def trigger_phase_two(self, ctx, boss):
        """Handles the 2.5x HP resurrection."""
        await ctx.send(f"⚠️ **{boss['name']}'s spirit is refusing to fade... IT'S EVOLVING!**")
        await asyncio.sleep(3)
        
        p2_hp = int(boss["max_hp"] * 2.5)
        await db.npcs.update_one(
            {"_id": boss["_id"]}, 
            {"$set": {"current_hp": p2_hp, "max_hp": p2_hp, "phase": 2}}
        )
        
        embed = discord.Embed(
            title=f"🔥 PHASE 2: {boss['name']} UNLEASHED",
            description=f"The boss has returned with **2.5x** more vitality and power!",
            color=0xFF0000
        )
        BannerManager.apply(embed, type="combat")
        await ctx.send(embed=embed)

    # --- PREFIX COMMANDS ---
    @commands.command(name="CE")
    async def ce(self, ctx, m: int = 1): await self.execute_attack(ctx, "CE", m)
    @commands.command(name="F")
    async def f(self, ctx, m: int = 1): await self.execute_attack(ctx, "F", m)
    @commands.command(name="W")
    async def w(self, ctx, m: int = 1): await self.execute_attack(ctx, "W", m)

async def setup(bot):
    await bot.add_cog(WorldBossCog(bot))
                 
