import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
from utils.checks import has_profile, not_in_combat

class DomainCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="domain_expand", description="🤞 Unleash your Domain Expansion (Requires 100 CE).")
    @has_profile()
    async def domain_expand(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})

        # 1. Validation: Technique and CE Cost
        ct_name = player.get("technique", "None")
        if ct_name == "None":
            return await interaction.response.send_message("❌ You lack an innate technique to expand.", ephemeral=True)

        if player.get("stats", {}).get("cur_ce", 0) < 100:
            return await interaction.response.send_message("❌ Insufficient Cursed Energy (100 required).", ephemeral=True)

        # 2. Fetch Domain Data
        ct_data = await db.techniques.find_one({"name": ct_name})
        domain = ct_data.get("domain")
        if not domain:
            return await interaction.response.send_message("❌ You have not manifested a Domain Expansion for this technique.", ephemeral=True)

        # 3. Apply Buffs and Deduct CE
        buffs = domain.get("buffs", {"hp": 0, "dmg": 0})
        await db.players.update_one(
            {"_id": user_id},
            {
                "$inc": {
                    "stats.cur_ce": -100,
                    "stats.current_hp": buffs["hp"],
                    "stats.dmg": buffs["dmg"]
                }
            }
        )

        embed = discord.Embed(
            title="🤞 DOMAIN EXPANSION",
            description=f"**{interaction.user.display_name}** manifests **{domain['name']}**!",
            color=0x000000
        )
        embed.add_field(name="Current Buffs", value=f"❤️ HP: `+{buffs['hp']}`\n💥 DMG: `+{buffs['dmg']}`")
        embed.set_footer(text="The sure-hit kill is now active.")
        
        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(DomainCog(bot))
  
