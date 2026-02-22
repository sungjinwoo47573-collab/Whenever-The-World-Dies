import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.checks import has_profile

class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="inventory", description="View your items and weapons.")
    @has_profile()
    async def inventory(self, interaction: discord.Interaction):
        player = await db.players.find_one({"_id": str(interaction.user.id)})
        items = player.get("inventory", [])
        
        item_list = "\n".join([f"• {i}" for i in items]) if items else "Empty"
        embed = discord.Embed(title="🎒 Your Inventory", description=item_list, color=0x2b2d31)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(InventoryCog(bot))
    
