import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
import asyncio
import random

class WorldBossCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_hp_bar(self, current_hp, max_hp):
        """Generates a 10-block HP bar with phase-based coloring."""
        percentage = (current_hp / max_hp) * 100
        filled_blocks = max(0, min(10, int(percentage / 10)))
        empty_blocks = 10 - filled_blocks
        
        if percentage > 65:
            color_emoji, color_hex = "🟩", 0x00FF00  # Phase 1
        elif percentage > 30:
            color_emoji, color_hex = "🟧", 0xFFA500  # Phase 2
        else:
            color_emoji, color_hex = "🟥", 0xFF0000  # Phase 3

        bar = (color_emoji * filled_blocks) + ("⬛" * empty_blocks)
        return f"{bar} `{percentage:.1f}%`", color_hex

    @app_commands.command(name="wb_create", description="Manifest a World Boss with 3 phases.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_create(self, interaction: discord.Interaction, name: str, url: str, hp: int, base_dmg: int):
        wb_data = {
            "name": name,
            "image": url,
            "max_hp": hp,
            "current_hp": hp,
            "is_world_boss": True,
            "base_dmg": base_dmg,
            "active": False
        }
        await db.npcs.update_one({"name": name}, {"$set": wb_data}, upsert=True)
        await interaction.response.send_message(f"🌍 **World Boss Registered:** {name}\nHP: {hp} | Base DMG: {base_dmg}")

    @app_commands.command(name="wb_skills", description="Assign kits to the World Boss.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_skills(self, interaction: discord.Interaction, name: str, technique: str, weapon: str, fighting_style: str):
        await db.npcs.update_one(
            {"name": name},
            {"$set": {"technique": technique, "weapon": weapon, "fighting_style": fighting_style}}
        )
        await interaction.response.send_message(f"⚔️ {name} is now armed with {technique}, {weapon}, and {fighting_style}.")

    @app_commands.command(name="wb_start", description="Begin the World Boss event in this channel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_start(self, interaction: discord.Interaction, name: str):
        boss = await db.npcs.find_one({"name": name, "is_world_boss": True})
        if not boss:
            return await interaction.response.send_message("❌ World Boss not found.")
        
        await interaction.response.send_message(f"🚨 **WARNING: {name} IS MANIFESTING!**")
        asyncio.create_task(self.world_boss_attack_loop(interaction.channel, name))

    async def world_boss_attack_loop(self, channel, boss_name):
        """Specialized AOE attack loop for World Bosses."""
        while True:
            boss = await db.npcs.find_one({"name": boss_name})
            if not boss or boss['current_hp'] <= 0:
                await channel.send(f"🎊 **{boss_name} HAS BEEN EXORCISED!** The world is safe... for now.")
                break

            # Calculate Phase & Damage Multiplier
            # Phase 1: 1.3x | Phase 2: 2.6x | Phase 3: 3.9x
            percentage = (boss['current_hp'] / boss['max_hp']) * 100
            if percentage > 65:
                phase, multiplier = 1, 1.3
            elif percentage > 30:
                phase, multiplier = 2, 2.6
            else:
                phase, multiplier = 3, 3.9

            # AOE Logic: Get all players in the channel
            targets = [m for m in channel.members if not m.bot]
            final_dmg = int(boss['base_dmg'] * multiplier)
            
            # Generate HP Bar Visual
            hp_bar, phase_color = self.generate_hp_bar(boss['current_hp'], boss['max_hp'])

            embed = discord.Embed(
                title=f"💥 WORLD BOSS ATTACK: {boss_name}",
                description=(
                    f"**Phase {phase} Intensity!**\n"
                    f"The boss strikes everyone for `{final_dmg}` damage!\n\n"
                    f"**Boss Health:**\n{hp_bar}\n`{boss['current_hp']}/{boss['max_hp']} HP`"
                ),
                color=phase_color
            )
            embed.set_thumbnail(url=boss['image'])
            await channel.send(embed=embed)

            # Apply damage to all targets in DB
            for target in targets:
                await db.players.update_one(
                    {"_id": str(target.id)},
                    {"$inc": {"stats.current_hp": -final_dmg}}
                )

            await asyncio.sleep(15) # Boss attacks every 15 seconds

async def setup(bot):
    await bot.add_cog(WorldBossCog(bot))
            
