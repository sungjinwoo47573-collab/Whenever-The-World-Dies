import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.embeds import JJKEmbeds
import random

class RerollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clan_reroll", description="Spend 1 reroll to manifest a new lineage.")
    async def clan_reroll(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})

        # 1. Check if player exists and has rerolls
        if not player:
            return await interaction.response.send_message("❌ You need to `/start` your journey first!", ephemeral=True)
        
        if player.get("clan_rerolls", 0) <= 0:
            return await interaction.response.send_message("❌ You have 0 rerolls! Use a code or wait for a giveaway.", ephemeral=True)

        # 2. Fetch the Clan Pool
        all_clans = await db.clans.find().to_list(length=100)
        if not all_clans:
            return await interaction.response.send_message("❌ The Zen'in, Gojo, and Kamo clans haven't been created yet by an admin!")

        # 3. Weighted Random Selection
        # This uses the 'roll_chance' (e.g., 0.01 for 1%) you set during /clan_create
        clans = [c for c in all_clans]
        weights = [c['roll_chance'] for c in clans]
        
        chosen_clan = random.choices(clans, weights=weights, k=1)[0]

        # 4. Apply New Clan and Deduct Reroll
        # We also clear the old clan buffs by resetting to base before applying new ones
        buffs = chosen_clan["buffs"]
        
        await db.players.update_one(
            {"_id": user_id},
            {
                "$set": {"clan": chosen_clan["name"]},
                "$inc": {
                    "clan_rerolls": -1,
                    "stats.max_hp": buffs.get("hp", 0),
                    "stats.max_ce": buffs.get("ce", 0),
                    "stats.dmg": buffs.get("dmg", 0)
                }
            }
        )

        # 5. Neon Success Embed
        embed = discord.Embed(
            title="🧬 Lineage Evolution",
            description=f"The sparks of black flash flicker as your soul reshapes...\n\nWelcome to the **{chosen_clan['name']}** Clan!",
            color=0x39FF14 # Neon Green
        )
        embed.add_field(name="Inherited Power", value=f"❤️ +{buffs['hp']} HP\n🧪 +{buffs['ce']} CE\n💥 +{buffs['dmg']} DMG")
        embed.set_footer(text=f"Rerolls remaining: {player['clan_rerolls'] - 1}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(RerollCog(bot))
  
