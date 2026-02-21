import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.checks import is_admin

class FightingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="fighting_create", description="Create a new Fighting Style (e.g., Black Flash Mastery, Martial Arts).")
    @is_admin()
    async def fighting_create(self, interaction: discord.Interaction, name: str, s1_name: str, s2_name: str, s3_name: str):
        """Registers the Fighting Style and its 3 skill names."""
        style_data = {
            "name": name,
            "skills": {
                "1": s1_name,
                "2": s2_name,
                "3": s3_name
            }
        }
        await db.fighting_styles.update_one({"name": name}, {"$set": style_data}, upsert=True)
        await interaction.response.send_message(f"👊 Fighting Style **{name}** created with skills: {s1_name}, {s2_name}, {s3_name}.")

    @app_commands.command(name="fighting_skill", description="Set the damage for fighting style skills.")
    @is_admin()
    async def fighting_skill_dmg(self, interaction: discord.Interaction, s1_dmg: int, s2_dmg: int, s3_dmg: int, style_name: str):
        """
        Sets the damage math for the 3 skills assigned to a style.
        This updates the global 'skills_library' so the combat engine can read it.
        """
        style = await db.fighting_styles.find_one({"name": style_name})
        if not style:
            return await interaction.response.send_message("❌ Fighting Style not found.")

        skills = style["skills"]
        dmgs = [s1_dmg, s2_dmg, s3_dmg]
        
        for i, (slot, name) in enumerate(skills.items()):
            await db.db["skills_library"].update_one(
                {"name": name},
                {"$set": {"name": name, "damage": dmgs[i], "effect": None}},
                upsert=True
            )

        await interaction.response.send_message(f"⚡ Damage set for **{style_name}** skills: {s1_dmg}, {s2_dmg}, {s3_dmg}.")

    @app_commands.command(name="fighting_remove", description="Remove a fighting style.")
    @is_admin()
    async def fighting_remove(self, interaction: discord.Interaction, name: str):
        await db.fighting_styles.delete_one({"name": name})
        await interaction.response.send_message(f"🗑️ Fighting Style **{name}** removed.")

async def setup(bot):
    await bot.add_cog(FightingCog(bot))
      
