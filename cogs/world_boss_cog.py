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

    def generate_hp_bar(self, current_hp, max_hp):
        """Generates a high-quality 10-block HP bar with phase-based coloring."""
        percentage = (current_hp / max_hp) * 100
        filled_blocks = max(0, min(10, int(percentage / 10)))
        empty_blocks = 10 - filled_blocks
        
        # Define Phase Visuals
        if percentage > 65:
            color_emoji, color_hex, phase_label = "🟩", 0x00FF00, "PHASE 1: STABLE"
        elif percentage > 30:
            color_emoji, color_hex, phase_label = "🟧", 0xFFA500, "PHASE 2: ENRAGED"
        else:
            color_emoji, color_hex, phase_label = "🟥", 0xFF0000, "PHASE 3: UNLEASHED"

        bar = (color_emoji * filled_blocks) + ("⬛" * empty_blocks)
        return f"{bar} `{percentage:.1f}%`", color_hex, phase_label

    @app_commands.command(name="wb_create", description="Admin: Register a 3-phase World Boss.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_create(self, interaction: discord.Interaction, name: str, url: str, hp: int, base_dmg: int):
        wb_data = {
            "name": name,
            "image": url,
            "max_hp": hp,
            "current_hp": 0, # Starts dormant
            "is_world_boss": True,
            "base_dmg": base_dmg,
            "active": False
        }
        await db.npcs.update_one({"name": name}, {"$set": wb_data}, upsert=True)
        
        embed = discord.Embed(title="📜 BOSS DATA REGISTERED", color=0x2ecc71)
        embed.add_field(name="Name", value=name, inline=True)
        embed.add_field(name="Total HP", value=f"`{hp:,}`", inline=True)
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="wb_start", description="Admin: Force start a World Boss event.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_start(self, interaction: discord.Interaction, name: str):
        boss = await db.npcs.find_one({"name": name, "is_world_boss": True})
        if not boss:
            return await interaction.response.send_message("❌ World Boss not found.")
        
        # Reset health for the event
        await db.npcs.update_one({"name": name}, {"$set": {"current_hp": boss["max_hp"]}})
        
        await interaction.response.send_message(f"🚨 **WARNING: {name} IS MANIFESTING!**")
        # Use the bot loop to create the background attack task
        self.bot.loop.create_task(self.world_boss_attack_loop(interaction.channel, name))

    async def world_boss_attack_loop(self, channel, boss_name):
        """AOE attack loop that scales damage based on Phases."""
        while True:
            boss = await db.npcs.find_one({"name": boss_name})
            
            # EXIT CONDITION: Boss defeated or deleted
            if not boss or boss.get('current_hp', 0) <= 0:
                victory_embed = discord.Embed(
                    title="🎊 THREAT EXORCISED",
                    description=f"**{boss_name}** has been banished. The area is secure.",
                    color=0x2ecc71
                )
                BannerManager.apply(victory_embed, type="main")
                await channel.send(embed=victory_embed)
                break

            # PHASE MULTIPLIERS
            percentage = (boss['current_hp'] / boss['max_hp']) * 100
            if percentage > 65:
                multiplier = 1.3
            elif percentage > 30:
                multiplier = 2.6
            else:
                multiplier = 3.9

            hp_bar, phase_color, phase_label = self.generate_hp_bar(boss['current_hp'], boss['max_hp'])
            final_dmg = int(boss['base_dmg'] * multiplier)

            # CONSTRUCT ATTACK EMBED
            embed = discord.Embed(
                title=f"💥 WORLD BOSS: {boss_name}",
                description=f"**{phase_label}**\nThe boss strikes everyone in the vicinity for `{final_dmg:,}` damage!",
                color=phase_color
            )
            embed.add_field(name="Boss Health", value=f"{hp_bar}\n`{boss['current_hp']:,}/{boss['max_hp']:,} HP`", inline=False)
            
            if "image" in boss:
                embed.set_thumbnail(url=boss['image'])
            
            BannerManager.apply(embed, type="combat")
            await channel.send(embed=embed)

            # Apply AOE damage to players (Targeting players with profiles)
            await db.players.update_many(
                {"stats.current_hp": {"$gt": 0}}, # Only hit players who are alive
                {"$inc": {"stats.current_hp": -final_dmg}}
            )

            await asyncio.sleep(20) # Attacking every 20s to reduce message spam

async def setup(bot):
    await bot.add_cog(WorldBossCog(bot))
                    
