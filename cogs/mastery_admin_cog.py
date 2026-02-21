import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.checks import is_admin

class MasteryAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_mastery", description="Set mastery for a specific Technique, Weapon, or Fighting Style.")
    @is_admin()
    async def set_mastery(self, interaction: discord.Interaction, user: discord.Member, category: str, name: str, amount: int):
        """
        Usage: /set_mastery user:@Sorcerer category:Technique name:Shrine amount:500
        Categories: technique, weapon, fighting_style
        """
        cat = category.lower()
        valid_cats = ["technique", "weapon", "fighting_style"]
        
        if cat not in valid_cats:
            return await interaction.response.send_message(f"❌ Invalid category. Use: {', '.join(valid_cats)}")

        user_id = str(user.id)
        # Update the mastery specifically for that item name
        # Example path: mastery.Shrine
        await db.players.update_one(
            {"_id": user_id},
            {"$set": {f"mastery.{name}": amount}}
        )

        await interaction.response.send_message(
            f"📈 Set **{user.display_name}'s** mastery for **{name}** ({cat}) to **{amount}**."
        )

    @app_commands.command(name="mastery_drop_set", description="Set how much mastery an NPC gives upon death.")
    @is_admin()
    async def mastery_drop_set(self, interaction: discord.Interaction, npc_name: str, amount: int):
        """Maps to the process_mastery_drop logic in systems/mastery_system.py"""
        result = await db.npcs.update_one(
            {"name": npc_name},
            {"$set": {"mastery_drop": amount}}
        )
        
        if result.matched_count > 0:
            await interaction.response.send_message(f"💀 **{npc_name}** will now drop **{amount}** mastery points upon exorcism.")
        else:
            await interaction.response.send_message("❌ NPC not found.")

async def setup(bot):
    await bot.add_cog(MasteryAdminCog(bot))
  
