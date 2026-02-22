import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.checks import is_admin
from utils.banner_manager import BannerManager

class TechAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ct_create", description="Admin: Create a base Cursed Technique.")
    @is_admin()
    async def ct_create(self, interaction: discord.Interaction, name: str, rarity: str, description: str):
        """Registers the main technique (e.g., 'Limitless')."""
        tech_data = {
            "name": name,
            "rarity": rarity,
            "description": description,
            "skills": [] # List of skill names linked to this CT
        }
        
        await db.techniques.update_one({"name": name}, {"$set": tech_data}, upsert=True)
        await interaction.response.send_message(f"✅ Cursed Technique **{name}** has been forged.")

    @app_commands.command(name="skill_add", description="Admin: Add a move to an existing Cursed Technique.")
    @is_admin()
    async def skill_add(
        self, 
        interaction: discord.Interaction, 
        ct_name: str, 
        skill_name: str, 
        damage_base: int, 
        ce_cost: int, 
        min_level: int = 1
    ):
        """Adds a move with specific damage and CE cost to a CT."""
        ct = await db.techniques.find_one({"name": ct_name})
        if not ct:
            return await interaction.response.send_message(f"❌ Technique '{ct_name}' not found.", ephemeral=True)

        skill_data = {
            "name": skill_name,
            "parent_ct": ct_name,
            "damage_base": damage_base,
            "ce_cost": ce_cost,
            "min_level": min_level
        }

        await db.skills.update_one({"name": skill_name}, {"$set": skill_data}, upsert=True)
        await db.techniques.update_one({"name": ct_name}, {"$push": {"skills": skill_name}})

        embed = discord.Embed(
            title="💥 Skill Registered",
            description=f"**{skill_name}** added to **{ct_name}**.",
            color=0x9b59b6
        )
        embed.add_field(name="Base DMG", value=f"`{damage_base}`", inline=True)
        embed.add_field(name="CE Cost", value=f"`{ce_cost}`", inline=True)
        
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(TechAdminCog(bot))
      
