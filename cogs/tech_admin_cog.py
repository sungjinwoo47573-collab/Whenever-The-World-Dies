import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
from utils.checks import is_admin

class TechAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tech_create", description="Admin: Register a new Cursed Technique with buffs.")
    @is_admin()
    async def tech_create(
        self, 
        interaction: discord.Interaction, 
        name: str, 
        rarity: str,
        ce_buff: float = 1.0, 
        dmg_buff: float = 1.0,
        description: str = "A powerful cursed technique."
    ):
        """
        Creates a technique. 
        Buffs act as multipliers (e.g., 1.5 = 50% boost).
        """
        tech_data = {
            "name": name,
            "rarity": rarity,
            "ce_buff": ce_buff,
            "dmg_buff": dmg_buff,
            "description": description
        }

        await db.techniques.update_one({"name": name}, {"$set": tech_data}, upsert=True)

        embed = discord.Embed(
            title="📜 Technique Scroll Registered",
            description=f"**{name}** has been added to the jujutsu archives.",
            color=0x9b59b6
        )
        embed.add_field(name="Rarity", value=rarity, inline=True)
        embed.add_field(name="Buffs", value=f"🧪 CE: x{ce_buff}\n💥 DMG: x{dmg_buff}", inline=True)
        
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(TechAdminCog(bot))
  
