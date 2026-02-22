import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager

class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_ping_role", description="Admin: Set the role to be notified when a World Boss appears.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_ping(self, interaction: discord.Interaction, role: discord.Role):
        """Saves the ping role ID to the guild's unique configuration."""
        guild_id = str(interaction.guild.id)
        
        await db.guild_config.update_one(
            {"_id": guild_id},
            {"$set": {"ping_role_id": role.id}},
            upsert=True
        )
        
        embed = discord.Embed(
            title="🔔 NOTIFICATION PROTOCOL",
            description=f"The veil has been tuned. {role.mention} will now be alerted when Cursed Spirits manifest.",
            color=0x3498db
        )
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="remove_ping", description="Admin: Disable role pings for Boss spawns.")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_ping(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        
        await db.guild_config.update_one(
            {"_id": guild_id}, 
            {"$unset": {"ping_role_id": ""}}
        )
        
        await interaction.response.send_message("🔕 Boss spawn notifications have been silenced.", ephemeral=True)

    @app_commands.command(name="stats_reset", description="Sorcerer: Reset your attributes to base levels to re-allocate Stat Points.")
    async def stats_reset(self, interaction: discord.Interaction):
        """Allows players to refund all spent points. Use a cost check if needed."""
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})

        if not player:
            return await interaction.response.send_message("❌ No profile found.", ephemeral=True)

        # Logic: Calculate total points the player should have based on their current level
        # Level 1 starts with 5, every level up adds 5. Total = Level * 5
        level = player.get("level", 1)
        total_points = level * 5
        
        # Reset to Base Stats (Grade 4 basics)
        # Note: We keep Clan Buffs separate in the actual logic, 
        # but this resets the points spent manually.
        await db.players.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "stats.max_hp": 500,
                    "stats.current_hp": 500,
                    "stats.max_ce": 100,
                    "stats.current_ce": 100,
                    "stats.dmg": 20,
                    "stat_points": total_points
                }
            }
        )

        embed = discord.Embed(
            title="♻️ SPIRITUAL RESET",
            description=(
                "You have performed a Binding Vow to reset your attributes.\n\n"
                f"**Points Refunded:** `{total_points}` SP\n"
                "**Status:** All attributes returned to Grade 4 baseline."
            ),
            color=0xe67e22
        )
        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
        
