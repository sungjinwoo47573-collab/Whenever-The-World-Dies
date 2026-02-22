import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
from utils.checks import has_profile
from systems.progression import get_rank

class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="start", description="Begin your journey as a Jujutsu Sorcerer.")
    async def start(self, interaction: discord.Interaction):
        """Initializes a new player profile with base stats."""
        user_id = str(interaction.user.id)
        existing = await db.players.find_one({"_id": user_id})

        if existing:
            return await interaction.response.send_message("⚠️ You already have a profile!", ephemeral=True)

        # Base starter data
        player_data = {
            "_id": user_id,
            "name": interaction.user.name,
            "level": 1,
            "xp": 0,
            "money": 500,
            "technique": "None",
            "clan": "None",
            "status": "idle",
            "stats": {
                "max_hp": 100,
                "current_hp": 100,
                "max_ce": 50,
                "cur_ce": 50,
                "dmg": 10,
                "spd": 5
            },
            "inventory": [],
            "mastery": {}
        }

        await db.players.insert_one(player_data)
        
        embed = discord.Embed(
            title="⛩️ Enrollment Complete",
            description="Welcome to Tokyo Jujutsu High. Your journey to the peak of the sorcery world begins now.",
            color=0x2b2d31
        )
        embed.add_field(name="Next Steps", value="Use `/roll_clan` to discover your lineage.")
        BannerManager.apply(embed, type="success")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile", description="Check your current stats and rank.")
    @has_profile()
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        """Displays the player's profile card."""
        target = member or interaction.user
        player = await db.players.find_one({"_id": str(target.id)})
        
        rank = await get_rank(player["level"])
        stats = player["stats"]

        embed = discord.Embed(
            title=f"👤 {target.display_name}'s Profile",
            color=0x2b2d31
        )
        embed.add_field(name="📊 Level", value=f"`Lv.{player['level']}` ({rank})", inline=True)
        embed.add_field(name="💰 Yen", value=f"`¥{player.get('money', 0):,}`", inline=True)
        embed.add_field(name="🌀 Clan", value=f"`{player.get('clan', 'None')}`", inline=True)
        
        # HP/CE Bars logic
        hp_bar = f"{stats['current_hp']}/{stats['max_hp']}"
        ce_bar = f"{stats['cur_ce']}/{stats['max_ce']}"
        
        embed.add_field(name="❤️ Health", value=f"`{hp_bar}`", inline=True)
        embed.add_field(name="✨ Cursed Energy", value=f"`{ce_bar}`", inline=True)
        embed.add_field(name="⚔️ Damage Stat", value=f"`{stats['dmg']}`", inline=True)

        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PlayerCog(bot))
        
