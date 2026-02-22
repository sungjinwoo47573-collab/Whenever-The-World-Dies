import discord
from discord import app_commands
from discord.ext import commands, tasks
from systems.backup import create_backup
from utils.checks import is_admin
from utils.banner_manager import BannerManager

class BackupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_backup.start() # Start automated backups

    def cog_unload(self):
        self.auto_backup.cancel()

    @tasks.loop(hours=24)
    async def auto_backup(self):
        """Automated daily backup."""
        await create_backup()
        print("💾 [System] Automated daily backup completed.")

    @app_commands.command(name="backup_now", description="Admin: Manually trigger a full database backup.")
    @is_admin()
    async def backup_now(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        timestamp, results = await create_backup()
        
        summary = "\n".join([f"📁 **{k}**: {v} entries" for k, v in results.items()])
        embed = discord.Embed(
            title="💾 Database Backup Complete",
            description=f"Snapshot ID: `{timestamp}`\n\n{summary}",
            color=0x2ecc71
        )
        BannerManager.apply(embed, type="admin")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BackupCog(bot))
  
