import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
from utils.checks import is_admin

class MasteryAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_mastery", description="Admin: Manually set mastery for a player's active kit.")
    @app_commands.choices(category=[
        app_commands.Choice(name="Cursed Technique", value="technique"),
        app_commands.Choice(name="Cursed Tool (Weapon)", value="weapon"),
        app_commands.Choice(name="Fighting Style", value="fighting_style")
    ])
    @is_admin()
    async def set_mastery(self, interaction: discord.Interaction, user: discord.Member, category: str, name: str, amount: int):
        """
        Force-sets mastery points for a specific item/style.
        Mastery is stored as mastery.ItemName to track individual proficiency.
        """
        user_id = str(user.id)
        # Directly update the mastery object inside the player document
        await db.players.update_one(
            {"_id": user_id},
            {"$set": {f"mastery.{name}": amount}}
        )

        embed = discord.Embed(
            title="📈 MASTERY CALIBRATION",
            description=f"The depth of **{user.display_name}'s** understanding has been altered.",
            color=0x9b59b6
        )
        embed.add_field(name="Subject", value=f"**{name}** ({category.replace('_', ' ').title()})", inline=True)
        embed.add_field(name="New Mastery", value=f"`{amount}` Points", inline=True)
        
        BannerManager.apply(embed, type="admin") #
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mastery_drop_set", description="Admin: Set mastery points rewarded for defeating an NPC.")
    @is_admin()
    async def mastery_drop_set(self, interaction: discord.Interaction, npc_name: str, amount: int):
        """Sets the mastery reward amount for NPCs (Standard or World Bosses)."""
        # Updates the NPC template so combat rewards are consistent
        result = await db.npcs.update_one(
            {"name": npc_name},
            {"$set": {"mastery_drop": amount}}
        )
        
        if result.matched_count > 0:
            embed = discord.Embed(
                title="💀 REWARD PROTOCOL UPDATED",
                description=f"Defeating **{npc_name}** now grants higher insight.",
                color=0xe74c3c
            )
            embed.add_field(name="Mastery Gain", value=f"`+{amount}` Points", inline=False)
            BannerManager.apply(embed, type="admin") #
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"❌ NPC **{npc_name}** not found in database.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MasteryAdminCog(bot))
    
