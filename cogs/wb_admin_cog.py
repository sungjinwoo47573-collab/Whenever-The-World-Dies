import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
from utils.checks import is_admin

class WorldBossAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="boss_moves", description="Admin: Assign Technique, Weapon, and Style to a Boss.")
    @is_admin()
    async def boss_moves(self, interaction: discord.Interaction, npc_name: str, technique: str, weapon: str, style: str):
        """Forces the Boss to use specific names for its reactive counter-attacks."""
        updates = {
            "technique": technique,
            "weapon": weapon,
            "fighting_style": style
        }
        
        result = await db.npcs.update_one(
            {"name": npc_name},
            {"$set": updates}
        )

        if result.matched_count > 0:
            embed = discord.Embed(
                title="👹 BOSS MOVESET SEALED", 
                description=f"**{npc_name}** will now retaliate using these styles.", 
                color=0xe74c3c
            )
            embed.add_field(name="Loadout", value=f"🌀 CT: {technique}\n⚔️ Weapon: {weapon}\n👊 Style: {style}")
            BannerManager.apply(embed, type="admin")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Boss not found in database.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(WorldBossAdminCog(bot))
    
