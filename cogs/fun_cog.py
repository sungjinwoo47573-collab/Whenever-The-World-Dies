import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_grade_from_level(self, level):
        """Standardized rank mapping to match FightingCog."""
        if level >= 80: return "Special Grade"
        if level >= 60: return "Grade 1"
        if level >= 40: return "Grade 2"
        if level >= 20: return "Grade 3"
        return "Grade 4"

    @app_commands.command(name="setlevel", description="Admin: Manually set a sorcerer's level and rank.")
    @app_commands.describe(user="The user to modify", level="The target level")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_level(self, interaction: discord.Interaction, user: discord.User, level: int):
        user_id = str(user.id)
        player = await db.players.find_one({"_id": user_id})

        if not player:
            return await interaction.response.send_message("❌ User has no profile.", ephemeral=True)

        # Logic: Recalculate rank and grant points based on new level
        new_grade = self.get_grade_from_level(level)
        stat_points = (level - 1) * 5
        
        await db.players.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "level": level,
                    "stat_points": stat_points,
                    "grade": new_grade,
                    "xp": 0,
                    # Full heal on manual level set
                    "stats.current_hp": player['stats']['max_hp'],
                    "stats.current_ce": player['stats']['max_ce']
                }
            }
        )

        embed = discord.Embed(
            title="🛠️ ARCHIVES UPDATED",
            description=f"The status of {user.mention} has been manually altered by the Higher-Ups.",
            color=0x2ecc71
        )
        embed.add_field(name="Level", value=f"`{level}`", inline=True)
        embed.add_field(name="Rank", value=f"`{new_grade}`", inline=True)
        embed.add_field(name="Total SP", value=f"`{stat_points}`", inline=True)

        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="addmoney", description="Admin: Deposit Yen into a player's account.")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_money(self, interaction: discord.Interaction, user: discord.User, amount: int):
        user_id = str(user.id)
        
        result = await db.players.update_one(
            {"_id": user_id}, 
            {"$inc": {"money": amount}}
        )

        if result.matched_count == 0:
            return await interaction.response.send_message("❌ Player profile not found.", ephemeral=True)

        embed = discord.Embed(
            title="💰 CURRENCY INJECTION",
            description=f"**¥{amount:,}** has been added to {user.mention}'s account.",
            color=0xf1c40f
        )
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(FunCog(bot))
    
