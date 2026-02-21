import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db

class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_ping_role")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_ping(self, interaction: discord.Interaction, role: discord.Role):
        await db.guild_config.update_one(
            {"_id": "settings"},
            {"$set": {"ping_role": role.id}},
            upsert=True
        )
        await interaction.response.send_message(f"🔔 Boss spawn pings set to {role.mention}")

    @app_commands.command(name="remove_ping")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_ping(self, interaction: discord.Interaction):
        await db.guild_config.update_one({"_id": "settings"}, {"$unset": {"ping_role": ""}})
        await interaction.response.send_message("🔕 Boss pings disabled.")

    @app_commands.command(name="stats_reset")
    async def stats_reset(self, interaction: discord.Interaction):
        # Implementation for manual reset (e.g., via item or cost)
        await db.players.update_one(
            {"_id": str(interaction.user.id)},
            {"$set": {"stats.max_hp": 100, "stats.max_ce": 50, "stats.dmg": 10, "stat_points": 0}}
        )
        await interaction.response.send_message("♻️ Your stats have been reset to Grade 4 basics.")

async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
  
