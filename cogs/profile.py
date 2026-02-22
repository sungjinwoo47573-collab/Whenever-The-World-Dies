import discord
from discord import app_commands
from discord.ext import commands
from database.crud import get_player, register_player, players_col
from config import create_embed, SUCCESS_COLOR

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="start", description="Begin your journey as a Jujutsu Sorcerer")
    async def start(self, interaction: discord.Interaction):
        success = await register_player(interaction.user.id)
        if success:
            embed = create_embed(
                "✨ Awakening", 
                f"Welcome to Jujutsu High, {interaction.user.mention}!\nYour potential as a sorcerer has been recognized. Use `/profile` to see your stats.",
                color=SUCCESS_COLOR
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("You are already registered, Sorcerer.", ephemeral=True)

    @app_commands.command(name="profile", description="Check your Sorcerer ID and stats")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        player = await get_player(target.id)

        if not player:
            return await interaction.response.send_message("This user is not a registered Sorcerer.", ephemeral=True)

        embed = create_embed(f"SORCERER ID: {target.display_name}", "", user=target)
        
        # Grid-style layout for high quality UI
        embed.add_field(name="📜 Rank", value=f"**Grade:** {player['grade']}\n**Level:** {player['level']}", inline=True)
        embed.add_field(name="💰 Wealth", value=f"**Money:** ¥{player['money']}", inline=True)
        embed.add_field(name="✨ Points", value=f"**Stat Points:** {player['stat_points']}", inline=True)
        
        stats_val = (
            f"❤️ **HP:** {player['hp']}/{player['max_hp']}\n"
            f"💥 **DMG:** {player['dmg']}\n"
            f"🌀 **CE:** {player['ce']}/{player['max_ce']}\n"
            f"⚡ **STM:** {player['stm']}/{player['max_stm']}"
        )
        embed.add_field(name="📊 Attributes", value=stats_val, inline=True)
        
        ability_val = (
            f"🔥 **Technique:** {player['cursed_technique']}\n"
            f"⚔️ **Weapon:** {player['weapon']}\n"
            f"🥊 **Style:** {player['fighting_style']}\n"
            f"🏯 **Domain:** {player['domain']}"
        )
        embed.add_field(name="🛡️ Mastery", value=ability_val, inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="distributestats", description="Use your stat points")
    @app_commands.describe(stat="Stat to upgrade", amount="Points to spend")
    @app_commands.choices(stat=[
        app_commands.Choice(name="HP", value="max_hp"),
        app_commands.Choice(name="DMG", value="dmg"),
        app_commands.Choice(name="CE", value="max_ce"),
        app_commands.Choice(name="STM", value="max_stm")
    ])
    async def distribute(self, interaction: discord.Interaction, stat: app_commands.Choice[str], amount: int):
        player = await get_player(interaction.user.id)
        if not player or player['stat_points'] < amount or amount <= 0:
            return await interaction.response.send_message("Invalid amount or insufficient points!", ephemeral=True)

        # Apply stat logic (e.g., 1 point = 10 HP, but 1 point = 2 DMG)
        multiplier = 10 if "max" in stat.value else 2
        gain = amount * multiplier

        await players_col.update_one(
            {"user_id": interaction.user.id},
            {"$inc": {stat.value: gain, "stat_points": -amount}}
        )

        await interaction.response.send_message(f"Successfully invested {amount} points into {stat.name} (+{gain}!)")

async def setup(bot):
    await bot.add_cog(Profile(bot))
      
