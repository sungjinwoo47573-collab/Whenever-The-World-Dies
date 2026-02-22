import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager

class NukeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="wipe_everything", 
        description="⚠️ ULTIMATE AUTHORITY: Erase all data across the entire Jujutsu database."
    )
    @commands.is_owner() # Restricted to the Bot Owner only
    async def wipe_everything(self, interaction: discord.Interaction, confirmation_phrase: str):
        """
        Total system reset. Deletes players, npcs, items, and the skills library.
        Safety Phrase: 'ERASE THE CURRENT ERA'
        """
        safety_phrase = "ERASE THE CURRENT ERA"
        
        if confirmation_phrase != safety_phrase:
            return await interaction.response.send_message(
                f"❌ **Safety Protocol Active.** To purge the world, you must type: `{safety_phrase}`", 
                ephemeral=True
            )

        # Deferring as bulk deletion in MongoDB can take a moment
        await interaction.response.defer(ephemeral=True)

        try:
            # 1. Syncing with all our rebuilt collections
            collections = [
                db.players, db.npcs, db.clans, db.items, 
                db.techniques, db.fighting_styles, db.codes, 
                db.raids, db.guild_config, db.skills, db.db["skills_library"]
            ]

            for collection in collections:
                await collection.delete_many({})

            # 2. Visual Announcement of the Reset
            nuke_embed = discord.Embed(
                title="🌌 THE VOID HAS CONSUMED THE WORLD",
                description=(
                    "The current era has reached its conclusion.\n\n"
                    "• All **Sorcerers** have been forgotten.\n"
                    "• All **Cursed Techniques** have faded.\n"
                    "• All **Manifestations** have been exorcised.\n\n"
                    "The world is now a blank canvas."
                ),
                color=0x000000 # Absolute Black
            )
            nuke_embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJqZndqZ3ZqZ3ZqZ3ZqZ3ZqZ3ZqZ3ZqZ3ZqZ3ZqZ3ZqZ3ZqJmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/vY009/giphy.gif") # Optional: A GIF of a white flash or explosion
            
            BannerManager.apply(nuke_embed, type="combat")
            
            await interaction.followup.send("💥 The database has been successfully purged.", ephemeral=True)
            await interaction.channel.send(embed=nuke_embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Critical Error during Purge: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(NukeCog(bot))
    
