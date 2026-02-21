import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db

class WorldBossListCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="worldbosslist", description="List all registered World Bosses and their configurations.")
    @app_commands.checks.has_permissions(administrator=True)
    async def world_boss_list(self, interaction: discord.Interaction):
        await interaction.response.defer() # Database lookups can be slow

        # Fetch all bosses
        bosses = await db.npcs.find({"is_world_boss": True}).to_list(length=50)

        if not bosses:
            return await interaction.followup.send("📭 No World Bosses found in the database. Use `/wb_create` first!")

        embed = discord.Embed(
            title="📂 World Boss Archives",
            description="A list of all registered threats and their current setup.",
            color=0x5865F2
        )

        for boss in bosses:
            # Check if URL looks valid to help you debug the Railway crash
            url = boss.get('image', 'No URL')
            url_status = "✅ Valid Format" if url.startswith("http") else "❌ BROKEN URL (Will Crash)"
            
            boss_info = (
                f"**HP:** `{boss.get('max_hp', 0):,}`\n"
                f"**Base DMG:** `{boss.get('base_dmg', 0)}`\n"
                f"**Technique:** `{boss.get('technique', 'None')}`\n"
                f"**URL:** [Link]({url}) | {url_status}"
            )
            
            embed.add_field(
                name=f"👹 {boss['name']}",
                value=boss_info,
                inline=False
            )

        embed.set_footer(text=f"Total Bosses: {len(bosses)}")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WorldBossListCog(bot))
  
