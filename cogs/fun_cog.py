import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="addmoney", description="Give Yen to a specific sorcerer.")
    @app_commands.describe(user="The user to receive money", amount="Amount of Yen to add")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_money(self, interaction: discord.Interaction, user: discord.User, amount: int):
        user_id = str(user.id)
        
        result = await db.players.update_one(
            {"_id": user_id},
            {"$inc": {"money": amount}}
        )

        if result.matched_count > 0:
            await interaction.response.send_message(f"💰 Deposited **¥{amount:,}** into {user.mention}'s account.")
        else:
            await interaction.response.send_message(f"❌ User {user.name} hasn't started their journey yet.", ephemeral=True)

    @app_commands.command(name="setlevel", description="Adjust a sorcerer's level.")
    @app_commands.describe(user="The user to level up", level="The new level to set")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_level(self, interaction: discord.Interaction, user: discord.User, level: int):
        user_id = str(user.id)
        
        result = await db.players.update_one(
            {"_id": user_id},
            {"$set": {"level": level}}
        )

        if result.matched_count > 0:
            await interaction.response.send_message(f"🆙 {user.mention} has been set to **Level {level}**.")
        else:
            await interaction.response.send_message(f"❌ User {user.name} not found in database.", ephemeral=True)

    @app_commands.command(name="addrerolls", description="Give clan rerolls to a user.")
    @app_commands.describe(user="The user to receive rerolls", amount="Number of rerolls")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_rerolls(self, interaction: discord.Interaction, user: discord.User, amount: int):
        user_id = str(user.id)
        
        result = await db.players.update_one(
            {"_id": user_id},
            {"$inc": {"clan_rerolls": amount}}
        )

        if result.matched_count > 0:
            await interaction.response.send_message(f"🧬 Granted **{amount}** Clan Rerolls to {user.mention}.")
        else:
            await interaction.response.send_message(f"❌ User {user.name} not found.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(FunCog(bot))
          
