import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
from utils.checks import is_admin, has_profile

class PromoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="code_create", description="Admin: Create a redeemable promo code.")
    @is_admin()
    async def code_create(self, interaction: discord.Interaction, code: str, rerolls: int, uses: int = 1):
        """
        Creates a code in the database.
        - rerolls: Number of clan rerolls granted.
        - uses: How many players can redeem this code before it expires.
        """
        code_data = {
            "code": code.upper(),
            "rerolls": rerolls,
            "max_uses": uses,
            "current_uses": 0,
            "redeemed_by": [] # List of user IDs who already used it
        }

        await db.codes.update_one({"code": code.upper()}, {"$set": code_data}, upsert=True)
        
        embed = discord.Embed(
            title="🎫 Promo Code Generated",
            description=f"Code: **{code.upper()}**\nRewards: **{rerolls} Clan Rerolls**\nLimit: **{uses} uses**",
            color=0x2ecc71
        )
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="redeem", description="Redeem a promo code for rewards.")
    @has_profile()
    async def redeem(self, interaction: discord.Interaction, code: str):
        user_id = str(interaction.user.id)
        code_upper = code.upper()

        # 1. Check if code exists
        code_doc = await db.codes.find_one({"code": code_upper})
        if not code_doc:
            return await interaction.response.send_message("❌ This code does not exist or has expired.", ephemeral=True)

        # 2. Check if user already redeemed it
        if user_id in code_doc.get("redeemed_by", []):
            return await interaction.response.send_message("❌ You have already redeemed this code!", ephemeral=True)

        # 3. Check if code has uses left
        if code_doc["current_uses"] >= code_doc["max_uses"]:
            return await interaction.response.send_message("❌ This code has reached its maximum use limit.", ephemeral=True)

        # 4. Atomic Update: Give rerolls and track the user
        reroll_amt = code_doc.get("rerolls", 1)
        
        # Update Player
        await db.players.update_one(
            {"_id": user_id},
            {"$inc": {"clan_rerolls": reroll_amt}}
        )

        # Update Code
        await db.codes.update_one(
            {"code": code_upper},
            {
                "$inc": {"current_uses": 1},
                "$push": {"redeemed_by": user_id}
            }
        )

        embed = discord.Embed(
            title="🎁 Reward Redeemed!",
            description=f"Successfully redeemed **{code_upper}**.\nAdded **{reroll_amt}** Clan Rerolls to your profile!",
            color=0xf1c40f
        )
        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PromoCog(bot))
      
