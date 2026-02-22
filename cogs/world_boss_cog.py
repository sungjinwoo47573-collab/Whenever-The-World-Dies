import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
import asyncio
import random
from utils.banner_manager import BannerManager

class WorldBossCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Visual settings for skill rarities
        self.rarities = {
            "Common": "⚪", 
            "Rare": "🔵", 
            "Epic": "🟣", 
            "Legendary": "🟡", 
            "Special Grade": "🔴"
        }

    def get_hp_visuals(self, current, max_hp, phase=1):
        """Generates a dynamic HP bar and identifies the current battle phase."""
        if max_hp <= 0: return "`[⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛]`", 0x000000, "PHASE 0"
        
        perc = (current / max_hp) * 100
        filled = max(0, min(10, int(perc / 10)))
        
        # Color and Label shift based on phase
        if phase == 1:
            color = 0x00FF00 # Green for Phase 1
            label = "PHASE 1: MORTAL"
            bar_emoji = "🟩"
        else:
            color = 0xFF0000 # Red for Phase 2
            label = "PHASE 2: ASCENDED"
            bar_emoji = "🟥"
            
        bar = f"`{bar_emoji * filled}{'⬛' * (10-filled)}` **{perc:.1f}%**"
        return bar, color, label

    # --- ADMIN COMMANDS ---

    @app_commands.command(name="wb_start", description="Admin: Manifest a World Boss in this channel.")
    @app_commands.describe(boss_name="The name of the NPC to summon")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_start(self, interaction: discord.Interaction, boss_name: str):
        """Cinematic manifestation of the World Boss."""
        await interaction.response.defer()
        
        npc = await db.npcs.find_one({"name": boss_name, "is_world_boss": True})
        if not npc:
            return await interaction.followup.send(f"❌ Boss '{boss_name}' not found.")

        # Reset Boss HP and Phase for a fresh encounter
        await db.npcs.update_one(
            {"_id": npc["_id"]},
            {"$set": {"current_hp": npc["max_hp"], "phase": 1}}
        )

        hp_bar, color, label = self.get_hp_visuals(npc["max_hp"], npc["max_hp"], phase=1)

        embed = discord.Embed(
            title=f"🚨 THE VEIL DROPS: {npc['name'].upper()}",
            description=(
                f"The entity **{npc['name']}** has entered the battlefield!\n\n"
                f"**Current Status:** {label}\n{hp_bar}\n\n"
                "**BATTLE PROTOCOL:**\n"
                "• Use `!CE`, `!F`, or `!W` to engage.\n"
                "• The boss will counter after every strike.\n"
                "• Exorcise the target to claim rewards."
            ),
            color=0xff0000
        )

        if npc.get("image"):
            embed.set_image(url=npc["image"])
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="wbdialogue", description="Admin: Set custom combat lines for a World Boss.")
    @app_commands.describe(
        name="Name of the boss",
        d1="Line 1", d2="Line 2", d3="Line 3", d4="Line 4"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_dialogue(self, interaction: discord.Interaction, name: str, d1: str, d2: str, d3: str, d4: str):
        """Sets the personality/quotes for the Boss counter-attacks."""
        dialogue_list = [d1, d2, d3, d4]
        
        result = await db.npcs.update_one(
            {"name": name, "is_world_boss": True},
            {"$set": {"custom_dialogue": dialogue_list}}
        )

        if result.matched_count == 0:
            return await interaction.response.send_message("❌ Boss not found.", ephemeral=True)

        await interaction.response.send_message(f"✅ Dialogue updated for **{name}**.", ephemeral=True)

    # --- COMBAT LOGIC ---

    async def boss_retaliation(self, ctx, boss):
        """Handles the 'Dialogue' style counter-attack logic."""
        # 1. Damage Math
        phase_mult = 2.5 if boss.get("phase", 1) == 2 else 1.0
        dmg = int(boss.get("base_dmg", 100) * phase_mult * random.uniform(0.95, 1.05))
        
        # 2. Dialogue Selection
        quotes = boss.get("custom_dialogue")
        if not quotes:
            quotes = ["“Stand proud. You are strong.”", "“Know your place.”", "“...Interesting.”"]
        
        quote = random.choice(quotes)
        
        # 3. Visuals
        hp_bar, color, label = self.get_hp_visuals(boss['current_hp'], boss['max_hp'], phase=boss.get("phase", 1))

        # 4. Message Construction
        msg = (
            f"**{boss['name']}**: {quote}\n"
            f"↳ *{boss['name']} retaliates with `{boss.get('technique', 'Cursed Strike')}` dealing `{dmg:,}` DMG to {ctx.author.mention}!*\n"
            f"{hp_bar}"
        )
        
        await ctx.send(msg)

        # Apply damage to player
        await db.players.update_one({"_id": str(ctx.author.id)}, {"$inc": {"stats.current_hp": -dmg}})

    async def execute_attack(self, ctx, category, move_num):
        """Main Player Strike logic with conversation-style flow."""
        user_id = str(ctx.author.id)
        player = await db.players.find_one({"_id": user_id})
        boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})

        if not player or not boss:
            return await ctx.send("🌑 The veil is quiet. No active World Boss to fight.")

        # 1. Loadout Check
        loadout_map = {"CE": "technique", "W": "weapon", "F": "fighting_style"}
        item_name = player.get("loadout", {}).get(loadout_map[category])

        if not item_name or item_name == "None":
            return await ctx.send(f"❌ You have no **{loadout_map[category]}** equipped!")

        # 2. Skill & Cost Check
        skill = await db.skills.find_one({"name": item_name, "move_number": move_num})
        if not skill:
            return await ctx.send(f"⚠️ Move {move_num} for `{item_name}` is not registered.")

        if category == "CE":
            cost = move_num * 15
            if player['stats']['current_ce'] < cost:
                return await ctx.send(f"⚠️ Insufficient CE! Need {cost}, you have {player['stats']['current_ce']}.")
            await db.players.update_one({"_id": user_id}, {"$inc": {"stats.current_ce": -cost}})

        # 3. Damage Calculation
        total_dmg = player['stats']['dmg'] + skill.get("damage", 0)
        new_hp = max(0, boss['current_hp'] - total_dmg)
        
        # Update Boss HP in DB
        await db.npcs.update_one({"_id": boss["_id"]}, {"$set": {"current_hp": new_hp}})
        
        # 4. Player Action Line
        emoji = self.rarities.get(skill.get("rarity", "Common"), "⚪")
        await ctx.send(f"⚔️ **{ctx.author.name}** uses {emoji} **{skill['move_title']}**! (`-{total_dmg:,}` HP)")

        # 5. Transition or Counter
        if new_hp <= 0:
            if boss.get("phase", 1) == 1:
                await self.trigger_phase_two(ctx, boss)
            else:
                await ctx.send(f"🎊 **{boss['name'].upper()} HAS BEEN EXORCISED!**")
        else:
            # Short delay for conversation flow
            await asyncio.sleep(1.5)
            boss['current_hp'] = new_hp # Update local object for the retaliation bar
            await self.boss_retaliation(ctx, boss)

    async def trigger_phase_two(self, ctx, boss):
        """Resurrects the boss into Phase 2."""
        await ctx.send(f"🚨 **{boss['name']} is reshaping its soul...**")
        await asyncio.sleep(3)
        
        p2_hp = int(boss["max_hp"] * 2.5)
        await db.npcs.update_one(
            {"_id": boss["_id"]}, 
            {"$set": {"current_hp": p2_hp, "max_hp": p2_hp, "phase": 2}}
        )
        
        embed = discord.Embed(
            title=f"🔥 PHASE 2: {boss['name'].upper()} ASCENDED",
            description=f"The entity has returned with **2.5x** Health and Damage!",
            color=0xFF0000
        )
        if boss.get("image"):
            embed.set_image(url=boss["image"])
        await ctx.send(embed=embed)

    # --- PREFIX COMMANDS ---
    @commands.command(name="CE")
    async def ce(self, ctx, m: int = 1): await self.execute_attack(ctx, "CE", m)
    @commands.command(name="W")
    async def w(self, ctx, m: int = 1): await self.execute_attack(ctx, "W", m)
    @commands.command(name="F")
    async def f(self, ctx, m: int = 1): await self.execute_attack(ctx, "F", m)

async def setup(bot):
    await bot.add_cog(WorldBossCog(bot))
                           
