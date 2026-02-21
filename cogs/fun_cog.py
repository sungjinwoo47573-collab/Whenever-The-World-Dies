import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_grade_from_level(self, level):
        """Helper to determine grade based on level."""
        if level >= 80: return "Special Grade Sorcerer"
        if level >= 60: return "Grade 1 Sorcerer"
        if level >= 40: return "Grade 2 Sorcerer"
        if level >= 20: return "Grade 3 Sorcerer"
        return "Grade 4 Sorcerer"

    @app_commands.command(name="setlevel", description="Set level and automatically update Grade and Stat Points.")
    @app_commands.describe(user="The user to modify", level="The target level")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_level(self, interaction: discord.Interaction, user: discord.User, level: int):
        user_id = str(user.id)
        
        # Calculate points (5 per level-up) and rank
        new_total_points = (level - 1) * 5
        new_grade = self.get_grade_from_level(level)
        
        await db.players.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "level": level,
                    "stat_points": new_total_points,
                    "grade": new_grade,
                    "xp": 0
                }
            }
        )

        embed = discord.Embed(
            title="🛠️ Admin Adjustment",
            description=f"Successfully updated {user.mention}.",
            color=0x2ecc71
        )
        embed.add_field(name="Level", value=f"`{level}`", inline=True)
        embed.add_field(name="Grade", value=f"`{new_grade}`", inline=True)
        embed.add_field(name="Points Granted", value=f"`{new_total_points}`", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="addmoney", description="Give Yen to a specific sorcerer.")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_money(self, interaction: discord.Interaction, user: discord.User, amount: int):
        user_id = str(user.id)
        await db.players.update_one({"_id": user_id}, {"$inc": {"money": amount}})
        await interaction.response.send_message(f"💰 Deposited **¥{amount:,}** for {user.mention}.")

async def setup(bot):
    await bot.add_cog(FunCog(bot))
    
