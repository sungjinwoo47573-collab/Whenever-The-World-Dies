import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
import asyncio

class WorldBossAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="wb_start", description="Admin: Force the active boss to start its AOE attack loop.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_start(self, interaction: discord.Interaction, name: str):
        """Finds a registered boss, sets their HP to max, and starts the combat loop."""
        boss = await db.npcs.find_one({"name": name, "is_world_boss": True})
        
        if not boss:
            return await interaction.response.send_message(f"❌ Boss `{name}` not found in the database.", ephemeral=True)

        # 1. Initialize Boss Health for the fight
        await db.npcs.update_one({"name": name}, {"$set": {"current_hp": boss["max_hp"]}})

        # 2. Announcement
        embed = discord.Embed(
            title="🚨 SPECIAL GRADE MANIFESTATION",
            description=f"**Entity:** {name}\n**Danger Level:** Extreme\n\n*The AOE attack cycle has begun. Sorcerers, prepare for battle!*",
            color=0xFF0000
        )
        if "image" in boss: embed.set_image(url=boss["image"])
        BannerManager.apply(embed, type="combat")
        
        await interaction.response.send_message(embed=embed)

        # 3. Trigger the Loop in WorldBossCog
        # We find the Cog and call the background task we built earlier
        combat_cog = self.bot.get_cog("WorldBossCog")
        if combat_cog:
            self.bot.loop.create_task(combat_cog.boss_attack_loop(interaction.channel, name))
        else:
            await interaction.followup.send("⚠️ Warning: `WorldBossCog` not loaded. Attack loop failed to start.")

    @app_commands.command(name="wb_ping", description="Admin: Ping the World Boss role or @everyone for an event.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_ping(self, interaction: discord.Interaction, message: str = "A Special Grade has appeared! All sorcerers report to the raid channel!"):
        """Sends a high-visibility ping to alert players to the raid."""
        # 1. Fetch the raid channel from settings
        config = await db.db["settings"].find_one({"setting": "wb_channel"})
        if not config:
            return await interaction.response.send_message("❌ Raid channel not set. Use `/wb_setup_channel` first.", ephemeral=True)
        
        channel = self.bot.get_channel(config.get("channel_id"))
        
        # 2. Construct the Alert
        embed = discord.Embed(
            title="📢 RAID CALL TO ARMS",
            description=message,
            color=0xF1C40F # Gold alert color
        )
        BannerManager.apply(embed, type="main")
        
        # 3. Send to the raid channel with @everyone (or a specific Role ID if you have one)
        if channel:
            await channel.send(content="@everyone", embed=embed)
            await interaction.response.send_message(f"✅ Raid alert sent to {channel.mention}!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Could not find the raid channel. Check permissions.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(WorldBossAdminCog(bot))
    
