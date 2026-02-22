import discord
from discord import app_commands
from discord.ext import commands
import random
from database.connection import db
from utils.banner_manager import BannerManager
from utils.checks import has_profile, is_admin

class ClanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clan_create", description="Admin: Register a new Clan into the database.")
    @is_admin()
    async def clan_create(self, interaction: discord.Interaction, name: str, rarity: str, hp_buff: int, ce_buff: int, dmg_buff: int, roll_chance: float):
        """Adds a clan to the global pool for players to roll."""
        clan_data = {
            "name": name,
            "rarity": rarity,
            "hp_buff": hp_buff,
            "ce_buff": ce_buff,
            "dmg_buff": dmg_buff,
            "roll_chance": roll_chance
        }
        # Fixed: Uses db.clans directly instead of subscripting db["clans"]
        await db.clans.update_one({"name": name}, {"$set": clan_data}, upsert=True)
        await interaction.response.send_message(f"✅ Clan **{name}** ({rarity}) has been added to the lineage pool.")

    @app_commands.command(name="roll_clan", description="Roll for a random sorcerer lineage (Costs 500 Yen).")
    @has_profile()
    async def roll_clan(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})

        if player.get("money", 0) < 500:
            return await interaction.response.send_message("❌ You need at least ¥500 to perform a lineage ritual.", ephemeral=True)

        # Fetch all available clans
        clans_cursor = db.clans.find({})
        all_clans = await clans_cursor.to_list(length=100)

        if not all_clans:
            return await interaction.response.send_message("⚠️ No clans have been created by the admins yet.", ephemeral=True)

        # Weighted random selection based on roll_chance
        weights = [c['roll_chance'] for c in all_clans]
        chosen_clan = random.choices(all_clans, weights=weights, k=1)[0]

        # Update player data with new clan and buffs
        await db.players.update_one(
            {"_id": user_id},
            {
                "$set": {"clan": chosen_clan['name']},
                "$inc": {
                    "money": -500,
                    "stats.max_hp": chosen_clan['hp_buff'],
                    "stats.max_ce": chosen_clan['ce_buff'],
                    "stats.dmg": chosen_clan['dmg_buff']
                }
            }
        )

        embed = discord.Embed(
            title="⛩️ Lineage Manifested",
            description=f"The blood of the **{chosen_clan['name']}** clan flows through you.",
            color=0x2ecc71
        )
        embed.add_field(name="Rarity", value=f"`{chosen_clan['rarity']}`")
        embed.add_field(name="Buffs", value=f"HP: +{chosen_clan['hp_buff']} | CE: +{chosen_clan['ce_buff']} | DMG: +{chosen_clan['dmg_buff']}")
        
        BannerManager.apply(embed, type="success")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ClanCog(bot))
    
