import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from systems.backup import create_backup, restore_from_file, BACKUP_DIR
from utils.checks import is_admin
from utils.banner_manager import BannerManager

class BackupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)

    @app_commands.command(name="backup_now", description="Admin: Manually trigger a full database backup.")
    @is_admin()
    async def backup_now(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        timestamp, results = await create_backup()
        
        summary = "\n".join([f"📁 **{k}**: {v} entries" for k, v in results.items()])
        await interaction.followup.send(f"✅ **Backup Created: `{timestamp}`**\n{summary}")

    @app_commands.command(name="backup_list", description="Admin: List all available backup files.")
    @is_admin()
    async def backup_list(self, interaction: discord.Interaction):
        if not os.path.exists(BACKUP_DIR) or not os.listdir(BACKUP_DIR):
            return await interaction.response.send_message("📭 No backups found.", ephemeral=True)
        
        files = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".json")]
        file_list = "\n".join([f"`{f}`" for f in files[-15:]]) # Show last 15
        await interaction.response.send_message(f"📂 **Available Backups:**\n{file_list}", ephemeral=True)

    @app_commands.command(name="backup_use", description="Admin: Restore a collection from a file.")
    @is_admin()
    async def backup_use(self, interaction: discord.Interaction, collection: str, file_name: str):
        await interaction.response.defer(ephemeral=True)
        count = await restore_from_file(collection, file_name)
        if count:
            await interaction.followup.send(f"✅ Restored **{count}** entries to `{collection}`.")
        else:
            await interaction.followup.send("❌ Restoration failed. Check filename/collection.")

    @app_commands.command(name="backup_delete", description="Admin: Delete a specific backup file.")
    @is_admin()
    async def backup_delete(self, interaction: discord.Interaction, file_name: str):
        file_path = os.path.join(BACKUP_DIR, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            await interaction.response.send_message(f"🗑️ Deleted `{file_name}`.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ File not found.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BackupCog(bot))
    
