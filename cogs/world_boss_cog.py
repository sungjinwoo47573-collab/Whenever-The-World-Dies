import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from systems.world_boss import calculate_wb_phase, get_aoe_targets
import asyncio

class WorldBossCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="wb_create", description="Manifest a World Boss.")
    async def wb_create(self, interaction: discord.Interaction, name: str, url: str, hp: int):
        wb_data = {
            "name": name,
            "image": url,
            "max_hp": hp,
            "current_hp": hp,
            "is_world_boss": True,
            "base_dmg": 50 # Default base
        }
        await db.npcs.update_one({"name": name}, {"$set": wb_data}, upsert=True)
        await interaction.response.send_message(f"🌍 **World Boss Registered:** {name} has appeared in the database.")

    @app_commands.command(name="world_boss_skills", description="Assign kits to the World Boss.")
    async def wb_skills(self, interaction: discord.Interaction, name: str, technique: str, weapon: str, fighting_style: str):
        await db.npcs.update_one(
            {"name": name},
            {"$set": {"technique": technique, "weapon": weapon, "fighting_style": fighting_style}}
        )
        await interaction.response.send_message(f"⚔️ {name} is now armed with {technique}, {weapon}, and {fighting_style}.")

    async def world_boss_attack_loop(self, channel, boss_name):
        """Specialized AOE attack loop for World Bosses."""
        while True:
            boss = await db.npcs.find_one({"name": boss_name})
            if not boss or boss['current_hp'] <= 0:
                break

            phase, multiplier = calculate_wb_phase(boss['current_hp'], boss['max_hp'])
            targets = get_aoe_targets(channel)
            
            # World Boss specialized damage (Base * 1.3 * Phase Multiplier)
            final_dmg = int(boss['base_dmg'] * 1.3 * multiplier)

            embed = discord.Embed(
                title=f"💥 WORLD BOSS ATTACK: Phase {phase}",
                description=f"**{boss_name}** unleashes an AOE strike, hitting **EVERYONE** for `{final_dmg}` DMG!",
                color=0xFF0000
            )
            await channel.send(embed=embed)

            # Apply damage to all players in DB
            for target in targets:
                await db.players.update_one(
                    {"_id": str(target.id)},
                    {"$inc": {"stats.current_hp": -final_dmg}}
                )

            await asyncio.sleep(15) # World boss attacks every 15s

async def setup(bot):
    await bot.add_cog(WorldBossCog(bot))
  
