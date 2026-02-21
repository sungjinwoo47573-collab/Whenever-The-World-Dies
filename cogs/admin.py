import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from database.models import npc_model, technique_model
from utils.checks import is_admin
from utils.embeds import JJKEmbeds

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="npc_create", description="[ADMIN] Create a new Curse or Boss for the world.")
    @app_commands.describe(
        name="Name of the NPC",
        hp="Maximum Health Points",
        dmg="Base Damage output",
        is_boss="Is this a boss? (faster attacks, better loot)",
        image_url="Link to the NPC image"
    )
    @is_admin()
    async def npc_create(self, interaction: discord.Interaction, name: str, hp: int, dmg: int, is_boss: bool, image_url: str):
        """Fused creator: Saves a new NPC blueprint to the database."""
        
        # Check if NPC already exists
        existing = await db.npcs.find_one({"name": name})
        if existing:
            return await interaction.response.send_message(
                embed=JJKEmbeds.error(f"An NPC named **{name}** already exists!"), ephemeral=True
            )

        # Create the data using our model
        new_npc = npc_model(name, is_boss, hp, dmg, image_url)
        
        # Save to MongoDB
        await db.npcs.insert_one(new_npc)

        embed = JJKEmbeds.success(
            "NPC Created", 
            f"Successfully added **{name}** to the Sorcerer Registry.\n"
            f"**Type:** {'Special Grade Boss' if is_boss else 'Standard Curse'}\n"
            f"**Stats:** ❤️ {hp} HP | 💥 {dmg} DMG"
        )
        embed.set_thumbnail(url=image_url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="tech_create", description="[ADMIN] Register a new Cursed Technique.")
    @is_admin()
    async def tech_create(self, interaction: discord.Interaction, name: str, rarity: str, cost: int):
        """Creates a technique shell. Slot mapping (!CE1-5) is added via /tech_edit."""
        # Simplified for now: maps name, rarity, and price.
        new_tech = technique_model(name, rarity, cost, slots={})
        await db.techniques.insert_one(new_tech)
        
        await interaction.response.send_message(
            f"📜 Technique **{name}** ({rarity}) has been added to the market records."
        )

# Required function for main.py to load this cog
async def setup(bot):
    await bot.add_cog(AdminCog(bot))
  
