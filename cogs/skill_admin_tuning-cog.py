import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
from utils.checks import is_admin

class SkillAdminTuningCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="weapon_skill_set", description="Admin: Map moves to !W1, !W2, and !W3 slots.")
    @is_admin()
    async def weapon_skills(self, interaction: discord.Interaction, weapon_name: str, 
                             s1_name: str, s1_dmg: int, 
                             s2_name: str, s2_dmg: int, 
                             s3_name: str, s3_dmg: int):
        """Maps weapon moves directly to the combat engine's skill library."""
        moves = [
            {"move_number": 1, "name": weapon_name, "move_title": s1_name, "damage": s1_dmg},
            {"move_number": 2, "name": weapon_name, "move_title": s2_name, "damage": s2_dmg},
            {"move_number": 3, "name": weapon_name, "move_title": s3_name, "damage": s3_dmg}
        ]
        
        for move in moves:
            await db.skills.update_one(
                {"name": move["name"], "move_number": move["move_number"]},
                {"$set": move},
                upsert=True
            )

        embed = discord.Embed(
            title="⚔️ WEAPON ARSENAL UPDATED",
            description=f"The moves for **{weapon_name}** are now live.",
            color=0x95a5a6
        )
        embed.add_field(name="Moveset", value=f"1. {s1_name}\n2. {s2_name}\n3. {s3_name}")
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(SkillAdminTuningCog(bot))
  
