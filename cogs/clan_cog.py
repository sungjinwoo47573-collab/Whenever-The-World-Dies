import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
import random

class ClanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roll_clan", description="Reroll your lineage. (Warning: Replaces current clan buffs)")
    async def roll_clan(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})

        if not player or player.get("clan_rerolls", 0) <= 0:
            return await interaction.response.send_message("❌ No rerolls available!", ephemeral=True)

        all_clans = await db.clans.find().to_list(length=100)
        if not all_clans:
            return await interaction.response.send_message("❌ No clans exist in the database.")

        # 1. Weighted Roll
        weights = [c['roll_chance'] for c in all_clans]
        chosen_clan = random.choices(all_clans, weights=weights, k=1)[0]
        
        # 2. Get OLD clan buffs to subtract them (prevent infinite stacking)
        old_clan_name = player.get("clan", "None")
        old_clan = await db.clans.find_one({"name": old_clan_name})
        old_buffs = old_clan.get("buffs", {"hp": 0, "ce": 0, "dmg": 0}) if old_clan else {"hp": 0, "ce": 0, "dmg": 0}

        # 3. Get NEW buffs
        new_buffs = chosen_clan.get("buffs", {"hp": 0, "ce": 0, "dmg": 0})

        # 4. Atomic Update: Remove old, Add new, Deduct reroll
        await db.players.update_one(
            {"_id": user_id},
            {
                "$set": {"clan": chosen_clan['name']},
                "$inc": {
                    "clan_rerolls": -1,
                    # Subtract old buffs, add new ones
                    "stats.max_hp": new_buffs['hp'] - old_buffs['hp'],
                    "stats.max_ce": new_buffs['ce'] - old_buffs['ce'],
                    "stats.dmg": new_buffs['dmg'] - old_buffs['dmg']
                }
            }
        )

        embed = discord.Embed(title="🧬 Lineage Roll", color=0x7289da, 
                              description=f"You are now a member of the **{chosen_clan['name']}** clan!")
        embed.add_field(name="New Stats", value=f"❤️ HP: +{new_buffs['hp']}\n🧪 CE: +{new_buffs['ce']}\n💥 DMG: +{new_buffs['dmg']}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ClanCog(bot))
    
