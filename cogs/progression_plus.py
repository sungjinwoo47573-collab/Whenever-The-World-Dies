import discord
from discord import app_commands
from discord.ext import commands
from database.connection import quests_col, players_col
from config import create_embed, SUCCESS_COLOR

class Quests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="createcharacterquests")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def create_quest(self, interaction: discord.Interaction, name: str, qtype: str, reward_style: str, grade_req: str):
        quest_data = {
            "name": name,
            "type": qtype, # Kill world boss, Raid, Collect
            "reward": reward_style,
            "required_grade": grade_req
        }
        await quests_col.update_one({"name": name}, {"$set": quest_data}, upsert=True)
        await interaction.response.send_message(f"Quest for **{name}** created.")

    @app_commands.command(name="questslist")
    async def quest_list(self, interaction: discord.Interaction):
        all_quests = await quests_col.find().to_list(length=50)
        embed = create_embed("📜 Available Quests", "Complete these to unlock new Fighting Styles.")
        for q in all_quests:
            embed.add_field(name=q['name'], value=f"Type: {q['type']}\nReq: {q['required_grade']}\nReward: {q['reward']}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Quests(bot))
  
