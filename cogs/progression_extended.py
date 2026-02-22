import discord
from discord import app_commands
from discord.ext import commands
from database.connection import quests_col, players_col, techniques_col
from config import create_embed, SUCCESS_COLOR

class ProgressionExtended(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="createcharacterquests", description="Admin: Create a Character Quest")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def create_quest(self, interaction: discord.Interaction, name: str, quest_type: str, reward_style: str, grade: str):
        quest_data = {
            "name": name,
            "type": quest_type, # Kill Boss, Raid, Collect Item
            "reward": reward_style,
            "required_grade": grade
        }
        await quests_col.update_one({"name": name}, {"$set": quest_data}, upsert=True)
        await interaction.response.send_message(f"Quest for **{name}** created.")

    @app_commands.command(name="leaderboard", description="View the top Sorcerers")
    async def leaderboard(self, interaction: discord.Interaction):
        # Sort by level first, then money
        top_players = await players_col.find().sort([("level", -1), ("money", -1)]).limit(10).to_list(length=10)
        
        description = ""
        for i, p in enumerate(top_players, 1):
            user = self.bot.get_user(p['user_id'])
            name = user.name if user else "Unknown Sorcerer"
            description += f"**{i}. {name}** - Lv.{p['level']} | ¥{p['money']}\n"

        embed = create_embed("🏆 GLOBAL LEADERBOARD", description or "No sorcerers found.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setreqmastery", description="Admin: Set mastery requirements for skills")
    async def set_mastery(self, interaction: discord.Interaction, tech_type: str, name: str, s1: int, s2: int, s3: int, s4: int):
        # tech_type: CT, Weapon, or FightingStyle
        await techniques_col.update_one(
            {"name": name},
            {"$set": {"req_s1": s1, "req_s2": s2, "req_s3": s3, "req_s4": s4}},
            upsert=True
        )
        await interaction.response.send_message(f"Mastery requirements set for {name}.")

async def setup(bot):
    await bot.add_cog(ProgressionExtended(bot))
  
