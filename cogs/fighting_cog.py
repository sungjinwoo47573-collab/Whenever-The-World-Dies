import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.checks import is_admin
from utils.banner_manager import BannerManager

class FightingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="style_create", description="Admin: Create a new Fighting Style.")
    @is_admin()
    async def style_create(self, interaction: discord.Interaction, name: str, description: str):
        """Registers a style like 'Black Flash' or 'Divergent Fist'."""
        style_data = {"name": name, "description": description}
        await db.db["styles"].update_one({"name": name}, {"$set": style_data}, upsert=True)
        await interaction.response.send_message(f"👊 Style **{name}** registered.")

async def setup(bot):
    await bot.add_cog(FightingCog(bot))
    
