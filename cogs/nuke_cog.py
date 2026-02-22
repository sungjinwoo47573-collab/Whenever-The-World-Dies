import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.checks import is_admin

class NukeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="nuke_database", description="⚠️ WARNING: Wipes all player data.")
    @is_admin()
    async def nuke_database(self, interaction: discord.Interaction, confirm: str):
        if confirm != "CONFIRM_RESET":
            return await interaction.response.send_message("❌ Verification failed. Type `CONFIRM_RESET`.", ephemeral=True)

        await db.players.delete_many({})
        await interaction.response.send_message("💥 Database purged. All players have been reset.")

async def setup(bot):
    await bot.add_cog(NukeCog(bot))
    
