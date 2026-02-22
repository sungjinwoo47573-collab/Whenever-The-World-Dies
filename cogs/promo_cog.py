import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.checks import has_profile, is_admin

class PromoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="redeem", description="Redeem a promo code for rewards.")
    @has_profile()
    async def redeem(self, interaction: discord.Interaction, code: str):
        promo = await db.codes.find_one({"code": code})
        if not promo:
            return await interaction.response.send_message("❌ Invalid code.", ephemeral=True)

        user_id = str(interaction.user.id)
        if user_id in promo.get("redeemed_by", []):
            return await interaction.response.send_message("❌ You've already used this code.", ephemeral=True)

        await db.players.update_one({"_id": user_id}, {"$inc": {"money": promo['reward']}})
        await db.codes.update_one({"code": code}, {"$push": {"redeemed_by": user_id}})
        
        await interaction.response.send_message(f"🎁 Redeemed! Received `¥{promo['reward']}`.")

async def setup(bot):
    await bot.add_cog(PromoCog(bot))
    
