import discord
from discord import app_commands
from discord.ext import commands
from utils.checks import is_admin

class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_rate = 1.0

    @app_commands.command(name="set_xp_rate", description="Admin: Change global XP gain multiplier.")
    @is_admin()
    async def set_xp(self, interaction: discord.Interaction, multiplier: float):
        self.xp_rate = multiplier
        await interaction.response.send_message(f"📈 XP Rate set to {multiplier}x")

async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
    
