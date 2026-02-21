import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from systems.progression import add_mastery
import random

class ClanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clan_reroll", description="Change your lineage using a reroll.")
    async def clan_reroll(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})

        if player.get("clan_rerolls", 0) <= 0:
            return await interaction.response.send_message("❌ You have no rerolls left! Use a code or buy more.", ephemeral=True)

        # Fetch all available clans
        all_clans = await db.clans.find().to_list(length=100)
        if not all_clans:
            return await interaction.response.send_message("❌ No clans registered in the database.")

        # Weighted Random Choice
        # Uses the 'roll_chance' set in /clan_create
        clans = [c for c in all_clans]
        weights = [c['roll_chance'] for c in clans]
        
        # Add a "Commoner" chance if weights don't equal 1.0
        chosen_clan = random.choices(clans, weights=weights, k=1)[0]

        # Apply Buffs to Player Stats
        buffs = chosen_clan["buffs"]
        await db.players.update_one(
            {"_id": user_id},
            {
                "$set": {"clan": chosen_clan["name"]},
                "$inc": {
                    "clan_rerolls": -1,
                    "stats.max_hp": buffs["hp"],
                    "stats.max_ce": buffs["ce"],
                    "stats.dmg": buffs["dmg"]
                }
            }
        )

        embed = discord.Embed(
            title="⛩️ Lineage Manifested",
            description=f"You are now a member of the **{chosen_clan['name']}** clan!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Inherited Buffs", value=f"❤️ +{buffs['hp']} HP\n🧪 +{buffs['ce']} CE\n💥 +{buffs['dmg']} DMG")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mastery_info", description="Check your mastery levels for skills.")
    async def mastery_info(self, interaction: discord.Interaction):
        player = await db.players.find_one({"_id": str(interaction.user.id)})
        mastery_data = player.get("mastery", {})

        if not mastery_data:
            return await interaction.response.send_message("📚 You haven't gained any mastery yet. Exorcise some curses!")

        embed = discord.Embed(title="📜 Mastery Records", color=discord.Color.blue())
        for skill, val in mastery_data.items():
            embed.add_field(name=skill, value=f"Level: {val}", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="set_mastery", description="Admin only: Manually set mastery for a player.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_mastery_cmd(self, interaction: discord.Interaction, user: discord.Member, skill_name: str, amount: int):
        await add_mastery(user.id, skill_name, amount)
        await interaction.response.send_message(f"✅ Set **{skill_name}** mastery for {user.display_name} to {amount}.")

async def setup(bot):
    await bot.add_cog(ClanCog(bot))
  
