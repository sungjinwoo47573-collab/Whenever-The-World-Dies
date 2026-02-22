import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_grade_from_level(self, level):
        """Standardized rank mapping to match Progression systems."""
        if level >= 80: return "Special Grade"
        if level >= 60: return "Grade 1"
        if level >= 40: return "Grade 2"
        if level >= 20: return "Grade 3"
        return "Grade 4"

    @app_commands.command(name="setlevel", description="Admin: Manually set a sorcerer's level and synchronize all vitals.")
    @app_commands.describe(user="The user to modify", level="The target level")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_level(self, interaction: discord.Interaction, user: discord.User, level: int):
        """Updates level, recalculates max stats, and performs a full heal/recharge."""
        user_id = str(user.id)
        player = await db.players.find_one({"_id": user_id})

        if not player:
            return await interaction.response.send_message("❌ User has no profile.", ephemeral=True)

        # 1. Logic: Recalculate Rank & Stat Points
        new_grade = self.get_grade_from_level(level)
        stat_points = (level - 1) * 5
        
        # 2. Logic: Recalculate Max Stats based on Level growth
        # Scaling: Base (500 HP / 100 CE) + 10 per level
        new_max_hp = 500 + (level * 10)
        new_max_ce = 100 + (level * 10)
        
        # 3. Database Update: Set level and SYNC current vitals to new maxes
        await db.players.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "level": level,
                    "stat_points": stat_points,
                    "grade": new_grade,
                    "xp": 0,
                    "stats.max_hp": new_max_hp,
                    "stats.current_hp": new_max_hp, # Full Heal
                    "stats.max_ce": new_max_ce,
                    "stats.current_ce": new_max_ce  # Full Recharge
                }
            }
        )

        embed = discord.Embed(
            title="🛠️ STATUS OVERWRITE: COMPLETE",
            description=f"The spiritual authority of {user.mention} has been manually realigned.",
            color=0x9b59b6
        )
        embed.add_field(name="Ascension", value=f"Level `{level}`\nRank: `{new_grade}`", inline=True)
        embed.add_field(name="Vitality Sync", value=f"❤️ `{new_max_hp}` HP\n🧪 `{new_max_ce}` CE", inline=True)
        embed.add_field(name="Resources", value=f"✨ `{stat_points}` SP", inline=True)

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
    
