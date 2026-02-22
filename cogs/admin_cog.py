import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.checks import is_admin
from utils.banner_manager import BannerManager

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="skill_buff", description="Admin: Globally adjust the base damage of a move.")
    @is_admin()
    async def skill_buff(self, interaction: discord.Interaction, move_name: str, new_damage: int):
        """Updates the library damage for a specific move, affecting all users."""
        result = await db.skills.update_one(
            {"move_title": move_name},
            {"$set": {"damage": new_damage}}
        )
        
        if result.matched_count > 0:
            embed = discord.Embed(title="⚖️ Balance Adjustment", description=f"**{move_name}** base damage set to `{new_damage}`.")
            BannerManager.apply(embed, type="admin")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Move not found.", ephemeral=True)

    @app_commands.command(name="give_yen", description="Admin: Award Yen to a player.")
    @is_admin()
    async def give_yen(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        await db.players.update_one({"_id": str(user.id)}, {"$inc": {"money": amount}})
        await interaction.response.send_message(f"✅ Added `¥{amount:,}` to {user.display_name}.")

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
        
