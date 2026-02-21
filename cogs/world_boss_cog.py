import discord
from discord.ext import commands
from database.connection import db
import asyncio
import random
from utils.banner_manager import BannerManager

class WorldBossCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Rarity Settings for Visuals/Buffs
        self.rarities = {
            "Common": {"color": 0x95a5a6, "emoji": "⚪"},
            "Rare": {"color": 0x3498db, "emoji": "🔵"},
            "Epic": {"color": 0x9b59b6, "emoji": "🟣"},
            "Legendary": {"color": 0xf1c40f, "emoji": "🟡"},
            "Special Grade": {"color": 0xe74c3c, "emoji": "🔴"}
        }

    def get_hp_visuals(self, current, max_hp, phase=1):
        """Generates the 3-Phase colored health bar and phase status."""
        perc = (current / max_hp) * 100
        filled = max(0, min(10, int(perc / 10)))
        
        # Phase 1 is Mortal, Phase 2 is Ascended (2.5x Power)
        color = 0x00FF00 if phase == 1 else 0xFF0000
        label = "PHASE 1: MORTAL" if phase == 1 else "PHASE 2: ASCENDED (2.5x)"
        bar = ("🟩" if phase == 1 else "🟥") * filled
        
        return f"{bar}{'⬛' * (10-filled)} `{perc:.1f}%`", color, label

    async def boss_retaliation(self, ctx, boss):
        """The Boss reacts ONLY after being hit. Includes 2-5% variance."""
        # 1. Random 2-5% Buff/Debuff Variance
        variance = random.uniform(0.95, 1.05)
        
        # 2. Phase Multiplier
        phase_mult = 2.5 if boss.get("phase", 1) == 2 else 1.0
        
        # 3. Final Damage Calculation
        final_dmg = int(boss.get("base_dmg", 100) * phase_mult * variance)
        
        # 4. Pick Boss Skill
        skills = [boss.get("technique"), boss.get("weapon"), boss.get("fighting_style")]
        active_skill = random.choice([s for s in skills if s]) or "Cursed Strike"

        hp_bar, color, label = self.get_hp_visuals(boss['current_hp'], boss['max_hp'], phase=boss.get("phase", 1))

        embed = discord.Embed(
            title=f"🚨 {boss['name']} COUNTER-ATTACKS!",
            description=(
                f"**{boss['name']}** unleashed **{active_skill.upper()}**!\n"
                f"💥 Damage to you: `{final_dmg:,}`\n"
                f"📊 Variance: `{variance:.1%}`"
            ),
            color=color
        )
        BannerManager.apply(embed, type="combat")
        await ctx.send(embed=embed)

        # Apply damage to the player
        await db.players.update_one({"_id": str(ctx.author.id)}, {"$inc": {"stats.current_hp": -final_dmg}})

    async def execute_attack(self, ctx, category, move_num):
        """Main Player Attack: Checks Loadout -> Skill Rarity -> Damage."""
        user_id = str(ctx.author.id)
        player = await db.players.find_one({"_id": user_id})
        boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})

        if not player or not boss:
            return await ctx.send("🌑 No active World Boss to fight.")

        # 1. FETCH LOADOUT
        loadout_map = {"CE": "technique", "W": "weapon", "F": "fighting_style"}
        active_item_name = player.get("loadout", {}).get(loadout_map[category])

        if not active_item_name:
            return await ctx.send(f"❌ You don't have a **{loadout_map[category]}** equipped! Use `/equip`.")

        # 2. CE COST CHECK
        if category == "CE":
            cost = move_num * 15
            if player.get("stats", {}).get("current_ce", 0) < cost:
                return await ctx.send(f"⚠️ Not enough CE! (Need {cost})")
            await db.players.update_one({"_id": user_id}, {"$inc": {"stats.current_ce": -cost}})

        # 3. DAMAGE CALC (Player Stats + Skill Data)
        skill_data = await db.skills.find_one({"name": active_item_name, "move_number": move_num})
        
        if not skill_data:
            return await ctx.send(f"⚠️ Move {move_num} for **{active_item_name}** is not registered.")

        # Rarity Multiplier for Skills
        rarity_name = skill_data.get("rarity", "Common")
        rarity_info = self.rarities.get(rarity_name, self.rarities["Common"])
        
        total_dmg = player.get("stats", {}).get("dmg", 10) + skill_data.get("damage", 0)

        # 4. APPLY DAMAGE
        new_hp = max(0, boss["current_hp"] - total_dmg)
        await db.npcs.update_one({"_id": boss["_id"]}, {"$set": {"current_hp": new_hp}})
        
        # 5. UI RESPONSE
        hp_bar, color, label = self.get_hp_visuals(new_hp, boss["max_hp"], phase=boss.get("phase", 1))
        
        embed = discord.Embed(
            title=f"⚔️ {ctx.author.name} ATTACKS!",
            description=(
                f"You used {rarity_info['emoji']} **{active_item_name}** (Move {move_num})\n"
                f"💥 Damage: `{total_dmg:,}`\n\n"
                f"**Boss HP:** {label}\n{hp_bar}"
            ),
            color=rarity_info['color']
        )
        BannerManager.apply(embed, type="combat")
        await ctx.send(embed=embed)

        # 6. HANDLE DEATH / TRANSITION / COUNTER
        if new_hp <= 0:
            if boss.get("phase", 1) == 1:
                await self.trigger_phase_two(ctx, boss)
            else:
                await ctx.send(f"🎊 **{boss['name']} HAS BEEN FULLY EXORCISED!**")
        else:
            # Boss counters immediately after player attack
            await asyncio.sleep(1)
            boss['current_hp'] = new_hp # Update local boss object for retaliation visual
            await self.boss_retaliation(ctx, boss)

    async def trigger_phase_two(self, ctx, boss):
        """Handles the 2.5x HP Phase 2 resurrection."""
        await ctx.send(f"⚠️ **{boss['name']} is manifesting its TRUE form...**")
        await asyncio.sleep(3)
        
        p2_hp = int(boss["max_hp"] * 2.5)
        await db.npcs.update_one(
            {"_id": boss["_id"]}, 
            {"$set": {"current_hp": p2_hp, "max_hp": p2_hp, "phase": 2}}
        )
        
        embed = discord.Embed(
            title=f"🔥 PHASE 2: {boss['name']} ASCENDED",
            description=f"The boss has returned with **2.5x** Health and Damage!",
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
        
