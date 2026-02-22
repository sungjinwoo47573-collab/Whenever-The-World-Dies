import discord
from discord import app_commands
from discord.ext import commands
import os
from systems.backup import restore_from_file, delete_backup_file, BACKUP_DIR
from utils.checks import is_admin
from utils.banner_manager import BannerManager

class BackupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="backup_list", description="Admin: List all available backup files.")
    @is_admin()
    async def backup_list(self, interaction: discord.Interaction):
        files = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".json")]
        if not files:
            return await interaction.response.send_message("📭 No backups found.", ephemeral=True)
        
        file_list = "\n".join([f"`{f}`" for f in files[:10]]) # Show last 10
        await interaction.response.send_message(f"📂 **Available Backups:**\n{file_list}", ephemeral=True)

    @app_commands.command(name="backup_use", description="Admin: Restore a collection from a file.")
    @is_admin()
    async def backup_use(self, interaction: discord.Interaction, collection: str, file_name: str):
        """Example: /backup_use collection:players file_name:players_20260222.json"""
        await interaction.response.defer(ephemeral=True)
        
        count = await restore_from_file(collection, file_name)
        if count:
            await interaction.followup.send(f"✅ Successfully restored **{count}** entries to `{collection}`.")
        else:
            await interaction.followup.send("❌ Restoration failed. Check the file name.")

    @app_commands.command(name="backup_delete", description="Admin: Delete a specific backup file.")
    @is_admin()
    async def backup_delete(self, interaction: discord.Interaction, file_name: str):
        if delete_backup_file(file_name):
            await interaction.response.send_message(f"🗑️ Deleted `{file_name}` successfully.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ File not found.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BackupCog(bot))
    
