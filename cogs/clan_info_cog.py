import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager

class ClanInfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="check_clan", description="View details and buffs of a specific clan.")
    async def check_clan(self, interaction: discord.Interaction, clan_name: str):
        # Case-insensitive search
        clan = await db.clans.find_one({"name": {"$regex": f"^{clan_name}$", "$options": "i"}})
        
        if not clan:
            return await interaction.response.send_message(f"❌ Clan **{clan_name}** not found.", ephemeral=True)

        chance = clan.get('roll_chance', 0.1) * 100
        embed = discord.Embed(
            title=f"⛩️ Clan Archives: {clan['name']}",
            description=f"**Rarity:** {clan.get('rarity', 'Unknown')}\n**Spawn Chance:** {chance}%",
            color=0x3498db
        )
        
        embed.add_field(
            name="💎 Multipliers",
            value=f"❤️ HP: `x{clan.get('hp_buff', 1.0)}`\n🧪 CE: `x{clan.get('ce_buff', 1.0)}`\n💥 DMG: `x{clan.get('dmg_buff', 1.0)}`",
            inline=False
        )
        
        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ClanInfoCog(bot))
  
