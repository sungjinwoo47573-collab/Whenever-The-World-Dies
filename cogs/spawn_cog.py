import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
import asyncio

class SpawnCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="force_spawn", description="Force a standard NPC to spawn in this channel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def force_spawn(self, interaction: discord.Interaction, npc_name: str):
        """Spawns a regular NPC from the database into the current channel."""
        npc = await db.npcs.find_one({"name": npc_name})
        
        if not npc:
            return await interaction.response.send_message(f"❌ NPC '{npc_name}' not found in database.", ephemeral=True)

        embed = discord.Embed(
            title="⚠️ CURSE MANIFESTATION",
            description=f"A level of cursed energy has coalesced! **{npc_name}** has appeared!",
            color=0x9b59b6
        )
        embed.set_image(url=npc.get("image", ""))
        embed.add_field(name="HP", value=f"❤️ {npc['max_hp']}/{npc['max_hp']}")
        
        await interaction.response.send_message(embed=embed)
        # Here you would trigger the NPC's specific attack loop if applicable

    @app_commands.command(name="force_wb", description="Force start a World Boss event.")
    @app_commands.checks.has_permissions(administrator=True)
    async def force_wb(self, interaction: discord.Interaction, boss_name: str):
        """Instantly starts the World Boss loop in the current channel."""
        boss = await db.npcs.find_one({"name": boss_name, "is_world_boss": True})

        if not boss:
            return await interaction.response.send_message(f"❌ World Boss '{boss_name}' not found.", ephemeral=True)

        # Reset HP for the new spawn
        await db.npcs.update_one(
            {"name": boss_name},
            {"$set": {"current_hp": boss["max_hp"]}}
        )

        await interaction.response.send_message(f"🚨 **EMERGENCY:** {boss_name} is descending upon this channel!")
        
        # Access the WorldBossCog to start the loop
        wb_cog = self.bot.get_cog("WorldBossCog")
        if wb_cog:
            asyncio.create_task(wb_cog.world_boss_attack_loop(interaction.channel, boss_name))
        else:
            await interaction.followup.send("❌ Error: WorldBossCog not loaded.")

async def setup(bot):
    await bot.add_cog(SpawnCog(bot))
  
