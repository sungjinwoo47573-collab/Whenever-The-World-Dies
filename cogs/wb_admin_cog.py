import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager

class WorldBossAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="wb_setup_channel", description="Set the raid channel for World Bosses.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_setup_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await db.db["settings"].update_one(
            {"setting": "wb_channel"},
            {"$set": {"channel_id": channel.id}},
            upsert=True
        )
        embed = discord.Embed(title="⚙️ SYSTEM CONFIG", description=f"Raid channel set: {channel.mention}", color=0x2b2d31)
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="wb_create", description="Register a Special Grade Boss.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_create(self, interaction: discord.Interaction, name: str, hp: int, base_dmg: int, image_url: str):
        boss_data = {
            "name": name, "max_hp": hp, "current_hp": 0,
            "base_dmg": base_dmg, "image": image_url, "is_world_boss": True
        }
        await db.npcs.update_one({"name": name}, {"$set": boss_data}, upsert=True)
        embed = discord.Embed(title="📜 BOSS REGISTERED", description=f"**{name}** added to library.", color=0x2ecc71)
        embed.set_thumbnail(url=image_url)
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="wb_skills", description="Assign techniques to the boss.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_skills(self, interaction: discord.Interaction, name: str, technique: str, weapon: str, style: str):
        await db.npcs.update_one(
            {"name": name},
            {"$set": {"technique": technique, "weapon": weapon, "fighting_style": style}}
        )
        await interaction.response.send_message(f"⚔️ {name} armed with {technique}, {weapon}, and {style}.")

async def setup(bot):
    await bot.add_cog(WorldBossAdminCog(bot))
    
