import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db

class NukeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="wipe_everything", 
        description="⚠️ EXTREME ACTION: Resets the entire bot database (Players, NPCs, Techniques, etc.)"
    )
    @commands.is_owner() # Strictly restricted to the Bot Owner
    async def wipe_everything(self, interaction: discord.Interaction, confirm: str):
        """
        Deletes all data across all collections.
        Requires the user to type 'CONFIRM TOTAL WIPE' exactly.
        """
        if confirm != "CONFIRM TOTAL WIPE":
            return await interaction.response.send_message(
                "❌ Safety Cancelled. You must type `CONFIRM TOTAL WIPE` exactly to proceed.", 
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        try:
            # Drop/Clear all major collections
            await db.players.delete_many({})
            await db.npcs.delete_many({})
            await db.clans.delete_many({})
            await db.items.delete_many({})
            await db.techniques.delete_many({})
            await db.fighting_styles.delete_many({})
            await db.codes.delete_many({})
            await db.raids.delete_many({})
            await db.guild_config.delete_many({})
            await db.db["skills_library"].delete_many({})

            # Send a public announcement of the rebirth
            nuke_embed = discord.Embed(
                title="🌌 THE WORLD HAS BEEN REBORN",
                description="The previous timeline has been erased. All sorcerers, curses, and techniques have ceased to exist.",
                color=0x000000
            )
            nuke_embed.set_footer(text="System Reset Complete.")
            
            await interaction.followup.send("💥 Database purged successfully.", ephemeral=True)
            await interaction.channel.send(embed=nuke_embed)

        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred during the wipe: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(NukeCog(bot))
  
