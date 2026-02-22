import discord
from discord.ext import commands
from database.connection import db
import asyncio
import random

class WorldBossCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rarities = {
            "Common": "⚪", "Rare": "🔵", "Epic": "🟣", 
            "Legendary": "🟡", "Special Grade": "🔴"
        }

    def generate_hp_bar(self, current, max_hp, phase=1):
        """Generates a visual health bar for the dialogue lines."""
        if max_hp <= 0: return "`[⬛⬛⬛⬛⬛]`"
        perc = (current / max_hp) * 100
        filled = max(0, min(10, int(perc / 10)))
        bar_emoji = "🟩" if phase == 1 else "🟥"
        return f"`{bar_emoji * filled}{'⬛' * (10-filled)}` **{perc:.1f}%**"

    @commands.command(name="wb_start")
    @commands.has_permissions(administrator=True)
    async def wb_start(self, ctx, boss_name: str):
        """Initial manifestation of the Boss."""
        npc = await db.npcs.find_one({"name": boss_name, "is_world_boss": True})
        if not npc: return await ctx.send("❌ Boss not found.")

        # Reset HP
        await db.npcs.update_one({"_id": npc["_id"]}, {"$set": {"current_hp": npc["max_hp"], "phase": 1}})

        embed = discord.Embed(
            title=f"🚨 THE VEIL DROPS: {npc['name'].upper()}",
            description=f"**{npc['name']}** has entered the battlefield.\n{self.generate_hp_bar(npc['max_hp'], npc['max_hp'])}",
            color=0xff0000
        )
        if npc.get("image"):
            embed.set_image(url=npc["image"])
        
        await ctx.send(embed=embed)

    async def boss_retaliation(self, ctx, boss):
        """The 'Dialogue' style counter-attack."""
        # 1. Logic
        phase_mult = 2.5 if boss.get("phase", 1) == 2 else 1.0
        dmg = int(boss.get("base_dmg", 100) * phase_mult * random.uniform(0.95, 1.05))
        
        # 2. Dialogue Selection
        quotes = [
            "“Stand proud. You are strong.”",
            "“You’re beginning to bore me, sorcerer.”",
            "“Know your place, fool!”",
            "“Is that all the cursed energy you can muster?”"
        ]
        quote = random.choice(quotes)
        
        # 3. Apply Damage to Player
        await db.players.update_one({"_id": str(ctx.author.id)}, {"$inc": {"stats.current_hp": -dmg}})

        # 4. SEND CONVERSATION STYLE MESSAGE
        hp_bar = self.generate_hp_bar(boss['current_hp'], boss['max_hp'], phase=boss.get("phase", 1))
        
        msg = (
            f"**{boss['name']}**: {quote}\n"
            f"↳ *{boss['name']} uses `{boss.get('technique', 'Strike')}` dealing `{dmg:,}` DMG to {ctx.author.mention}!*\n"
            f"{hp_bar}"
        )
        await ctx.send(msg)

    async def execute_attack(self, ctx, category, move_num):
        """Clean player attack line followed by Boss retaliation."""
        user_id = str(ctx.author.id)
        player = await db.players.find_one({"_id": user_id})
        boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})

        if not player or not boss:
            return await ctx.send("🌑 The battlefield is empty.")

        # 1. Fetch Skill & Loadout
        loadout_key = {"CE": "technique", "W": "weapon", "F": "fighting_style"}[category]
        item_name = player.get("loadout", {}).get(loadout_key)
        
        if not item_name: return await ctx.send(f"❌ No {loadout_key} equipped.")

        skill = await db.skills.find_one({"name": item_name, "move_number": move_num})
        if not skill: return await ctx.send("⚠️ Move not found.")

        # 2. CE Cost Check
        if category == "CE":
            cost = move_num * 15
            if player['stats']['current_ce'] < cost:
                return await ctx.send(f"⚠️ Insufficient CE! ({player['stats']['current_ce']}/{cost})")
            await db.players.update_one({"_id": user_id}, {"$inc": {"stats.current_ce": -cost}})

        # 3. Damage Logic
        dmg = player['stats']['dmg'] + skill['damage']
        new_hp = max(0, boss['current_hp'] - dmg)
        await db.npcs.update_one({"_id": boss["_id"]}, {"$set": {"current_hp": new_hp}})

        # 4. PLAYER ACTION LINE
        emoji = self.rarities.get(skill.get("rarity", "Common"), "⚪")
        await ctx.send(f"⚔️ **{ctx.author.name}** uses {emoji} **{skill['move_title']}**! (`-{dmg:,}` HP)")

        # 5. BOSS COUNTER
        if new_hp > 0:
            await asyncio.sleep(1.5)
            boss['current_hp'] = new_hp # Sync for the visual
            await self.boss_retaliation(ctx, boss)
        else:
            await ctx.send(f"🎊 **{boss['name']} has been exorcised!**")

    @commands.command(name="CE")
    async def ce(self, ctx, m: int = 1): await self.execute_attack(ctx, "CE", m)
    @commands.command(name="W")
    async def w(self, ctx, m: int = 1): await self.execute_attack(ctx, "W", m)
    @commands.command(name="F")
    async def f(self, ctx, m: int = 1): await self.execute_attack(ctx, "F", m)

async def setup(bot):
    await bot.add_cog(WorldBossCog(bot))
        
