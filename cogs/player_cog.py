import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from database.models import player_model
from utils.embeds import JJKEmbeds
from utils.checks import not_in_combat

class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="start", description="Begin your journey as a Grade 4 Sorcerer.")
    async def start(self, interaction: discord.Interaction):
        """Creates a new profile in the database."""
        user_id = str(interaction.user.id)
        
        # Check if they already have a profile
        existing = await db.players.find_one({"_id": user_id})
        if existing:
            return await interaction.response.send_message(
                "❌ You are already registered in the Sorcerer records!", ephemeral=True
            )

        # Create new data and save
        new_data = player_model(user_id, interaction.user.display_name)
        await db.players.insert_one(new_data)

        # Send welcome UI
        embed = JJKEmbeds.success(
            "Welcome, Sorcerer", 
            f"Registration complete for **{interaction.user.name}**.\n"
            "You have been assigned the rank: `Grade 4 Sorcerer`."
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile", description="View your current stats, grade, and loadout.")
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        """Fetches and displays player data using the JJK visual template."""
        target = member or interaction.user
        data = await db.players.find_one({"_id": str(target.id)})

        if not data:
            return await interaction.response.send_message("❌ This user is not a registered Sorcerer.", ephemeral=True)

        embed = JJKEmbeds.profile(data)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="upgrade", description="Spend stat points to increase your power.")
    @app_commands.describe(stat="Which stat to increase? (hp, ce, dmg)")
    @not_in_combat()
    async def upgrade(self, interaction: discord.Interaction, stat: str):
        """Increases a specific stat if the player has points available."""
        stat = stat.lower()
        if stat not in ["hp", "ce", "dmg"]:
            return await interaction.response.send_message("❌ Valid stats are: `hp`, `ce`, `dmg`.", ephemeral=True)

        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})

        if player.get("stat_points", 0) < 1:
            return await interaction.response.send_message("❌ You don't have any Stat Points! Level up first.", ephemeral=True)

        # Update logic: 1 pt = +10 HP/CE or +2 DMG
        inc_val = 10 if stat in ["hp", "ce"] else 2
        field_path = f"stats.{stat}"
        
        # If upgrading HP/CE, also increase the 'max' value
        update_query = {"$inc": {"stat_points": -1, field_path: inc_val}}
        if stat in ["hp", "ce"]:
            update_query["$inc"][f"stats.max_{stat}"] = inc_val

        await db.players.update_one({"_id": user_id}, update_query)
        
        await interaction.response.send_message(
            embed=JJKEmbeds.success("Stat Upgraded", f"Successfully increased your **{stat.upper()}**!")
        )

async def setup(bot):
    await bot.add_cog(PlayerCog(bot))
  
