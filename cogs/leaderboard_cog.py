import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="View the top sorcerers by Grade or Wealth.")
    @app_commands.choices(category=[
        app_commands.Choice(name="Grade (Power)", value="grade"),
        app_commands.Choice(name="Wealth (Yen)", value="money")
    ])
    async def leaderboard(self, interaction: discord.Interaction, category: str):
        await interaction.response.defer() # Database queries can take a second
        
        if category == "money":
            # Sort by money descending
            players = await db.players.find().sort("money", -1).limit(10).to_list(10)
            title = "💰 Wealthiest Sorcerers"
            field_name = "Balance"
            
            description = ""
            for i, p in enumerate(players, 1):
                description += f"**{i}. {p['name']}** — ¥{p['money']:,}\n"

        else:
            # Sort by grade_level descending (assuming 5 is Special Grade, 1 is Grade 4)
            players = await db.players.find().sort("grade_level", -1).limit(10).to_list(10)
            title = "⛩️ Highest Graded Sorcerers"
            field_name = "Grade"
            
            description = ""
            for i, p in enumerate(players, 1):
                description += f"**{i}. {p['name']}** — `{p['grade']}`\n"

        embed = discord.Embed(
            title=title,
            description=description or "No sorcerers found in the archives.",
            color=0x7289da
        )
        embed.set_footer(text="The strong define the era.")
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LeaderboardCog(bot))
  
