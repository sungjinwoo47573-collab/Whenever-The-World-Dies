import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.checks import is_admin
from utils.banner_manager import BannerManager

class TechAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ct_create", description="Admin: Forge a new innate Cursed Technique.")
    @is_admin()
    async def ct_create(self, interaction: discord.Interaction, name: str, rarity: str, description: str):
        """Registers the main power source (e.g., 'Ten Shadows')."""
        tech_data = {
            "name": name,
            "rarity": rarity,
            "description": description,
            "skills": [] # List of skill names linked to this CT
        }
        
        # Uses direct db connection to prevent subscriptable errors
        await db.techniques.update_one({"name": name}, {"$set": tech_data}, upsert=True)
        
        embed = discord.Embed(
            title="🌀 Technique Manifested",
            description=f"**{name}** has been added to the world archives.",
            color=0x9b59b6
        )
        embed.add_field(name="Rarity", value=f"`{rarity}`")
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="skill_add", description="Admin: Add a combat move to an existing Technique.")
    @is_admin()
    async def skill_add(
        self, 
        interaction: discord.Interaction, 
        ct_name: str, 
        skill_name: str, 
        damage: int, 
        ce_cost: int, 
        min_level: int = 1
    ):
        """Adds a specific attack/skill to a CT with damage and level requirements."""
        ct = await db.techniques.find_one({"name": ct_name})
        if not ct:
            return await interaction.response.send_message(f"❌ Technique '{ct_name}' not found.", ephemeral=True)

        skill_data = {
            "move_title": skill_name, # Used by the Damage Engine
            "parent_ct": ct_name,
            "damage": damage,
            "ce_cost": ce_cost,
            "min_level": min_level
        }

        # Update the skills collection and link it to the main Technique
        await db.skills.update_one({"move_title": skill_name}, {"$set": skill_data}, upsert=True)
        await db.techniques.update_one({"name": ct_name}, {"$addToSet": {"skills": skill_name}})

        embed = discord.Embed(
            title="💥 Skill Registered",
            description=f"**{skill_name}** added to **{ct_name}**.",
            color=0x00fbff
        )
        embed.add_field(name="Stats", value=f"DMG: `{damage}` | CE: `{ce_cost}` | Lv: `{min_level}`")
        
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(TechAdminCog(bot))
    
