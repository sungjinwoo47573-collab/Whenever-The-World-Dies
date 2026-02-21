import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db

class WorldBossAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="worldbosslist", description="List all registered World Bosses and check for broken URLs.")
    async def world_boss_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Pulling from the NPC collection where is_world_boss is True
        bosses = await db.npcs.find({"is_world_boss": True}).to_list(length=50)

        if not bosses:
            return await interaction.followup.send("📭 No World Bosses found. Use `/wb_create` to add one!")

        embed = discord.Embed(title="📂 World Boss Archives", color=0x5865F2)

        for boss in bosses:
            url = boss.get('image', 'No URL')
            # Check for the error that crashed your Railway logs
            url_status = "✅ Valid" if url.startswith("http") else "❌ BROKEN (Delete this)"
            
            embed.add_field(
                name=f"👹 {boss['name']}",
                value=f"**HP:** `{boss.get('max_hp', 0):,}`\n**URL:** {url_status}\n[View Image]({url})",
                inline=False
            )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="wb_delete", description="Remove a World Boss from the database.")
    @app_commands.describe(name="The exact name of the boss to delete")
    async def wb_delete(self, interaction: discord.Interaction, name: str):
        result = await db.npcs.delete_one({"name": name, "is_world_boss": True})
        
        if result.deleted_count > 0:
            await interaction.response.send_message(f"🗑️ **{name}** has been erased from existence.")
        else:
            await interaction.response.send_message(f"❓ Could not find a World Boss named `{name}`.")

# --- THE MISSING PART THAT WAS CAUSING YOUR ERROR ---
async def setup(bot):
    await bot.add_cog(WorldBossAdminCog(bot))
  
