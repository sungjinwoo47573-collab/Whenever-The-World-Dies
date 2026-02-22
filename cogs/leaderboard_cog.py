import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="View the elite ranking of Jujutsu Sorcerers.")
    @app_commands.choices(category=[
        app_commands.Choice(name="Grade (Level/Power)", value="level"),
        app_commands.Choice(name="Wealth (Total Yen)", value="money")
    ])
    async def leaderboard(self, interaction: discord.Interaction, category: str):
        """Displays the top 10 sorcerers in the specified category."""
        # Deferring is crucial for database queries to prevent interaction expiration
        await interaction.response.defer() 
        
        # Mapping for visual flair
        crowns = {1: "🥇", 2: "🥈", 3: "🥉"}
        
        if category == "money":
            # Sort by money descending
            cursor = db.players.find().sort("money", -1).limit(10)
            players = await cursor.to_list(length=10)
            title = "💰 FINANCIAL ARCHIVES: TOP WEALTH"
            color = 0xf1c40f # Gold
            
            description = ""
            for i, p in enumerate(players, 1):
                icon = crowns.get(i, f"`#{i}`")
                money = p.get('money', 0)
                description += f"{icon} **{p.get('name', 'Unknown')}** — ¥{money:,}\n"

        else:
            # Sort by Level (Power) descending
            cursor = db.players.find().sort("level", -1).limit(10)
            players = await cursor.to_list(length=10)
            title = "⛩️ SORCERER HIERARCHY: TOP GRADES"
            color = 0xe74c3c # Red (Danger/Power)
            
            description = ""
            for i, p in enumerate(players, 1):
                icon = crowns.get(i, f"`#{i}`")
                level = p.get('level', 1)
                grade = p.get('grade', 'Grade 4')
                description += f"{icon} **{p.get('name', 'Unknown')}** (Lvl {level}) — `{grade}`\n"

        embed = discord.Embed(
            title=title,
            description=description or "*The archives are empty. No sorcerers have made their mark yet.*",
            color=color
        )
        
        embed.set_footer(text="The strong define the balance of the world.")
        BannerManager.apply(embed, type="main")
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LeaderboardCog(bot))
                
