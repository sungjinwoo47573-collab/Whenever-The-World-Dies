import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db

class BossConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="wb_spawn_channel", description="Set the current channel as the official World Boss Arena.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_wb_channel(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id
        
        # Save the channel ID to a settings collection
        await db.db["settings"].update_one(
            {"setting": "wb_channel"},
            {"$set": {"channel_id": channel_id}},
            upsert=True
        )
        
        await interaction.response.send_message(
            f"🏟️ **Arena Set!** World Bosses will now automatically manifest in {interaction.channel.mention} every 10 minutes."
        )

async def setup(bot):
    await bot.add_cog(BossConfigCog(bot))
  
