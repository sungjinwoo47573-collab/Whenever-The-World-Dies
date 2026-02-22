import discord
from discord import app_commands
from discord.ext import commands
import os
import json
from datetime import datetime
from database.connection import db
from utils.checks import is_admin
from utils.banner_manager import BannerManager

class BackupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.backup_path = "./backups"

    @app_commands.command(name="backup_now", description="Admin: Force a manual backup of all game data.")
    @is_admin()
    async def backup_now(self, interaction: discord.Interaction):
        """Dumps all MongoDB collections into timestamped JSON files."""
        await interaction.response.defer(ephemeral=True)
        
        if not os.path.exists(self.backup_path):
            os.makedirs(self.backup_path)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        collections = ["players", "clans", "techniques", "skills", "npcs", "items"]
        summary = []

        for col_name in collections:
            try:
                # Direct access via the Database class shortcuts
                collection = getattr(db, col_name)
                cursor = collection.find({})
                data = await cursor.to_list(length=None)
                
                filename = f"{col_name}_{timestamp}.json"
                file_full_path = os.path.join(self.backup_path, filename)
                
                with open(file_full_path, "w") as f:
                    json.dump(data, f, indent=4, default=str)
                
                summary.append(f"✅ {col_name.capitalize()}: {len(data)} entries")
            except Exception as e:
                summary.append(f"❌ {col_name.capitalize()}: Error ({e})")

        embed = discord.Embed(
            title="💾 System Backup Initiated",
            description="\n".join(summary),
            color=0x00fbff
        )
        BannerManager.apply(embed, type="admin")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="backup_list", description="Admin: List available backup files.")
    @is_admin()
    async def backup_list(self, interaction: discord.Interaction):
        """Shows the most recent files in the backups directory."""
        if not os.path.exists(self.backup_path):
            return await interaction.response.send_message("📂 No backups directory found.", ephemeral=True)

        files = sorted(os.listdir(self.backup_path), reverse=True)[:10]
        file_list = "\n".join([f"`{f}`" for f in files]) or "No files found."

        embed = discord.Embed(title="📂 Recent Backups", description=file_list)
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(BackupCog(bot))
                
