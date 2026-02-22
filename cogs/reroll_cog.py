import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
import random

class RerollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clan_reroll", description="Spend 1 reroll to rewrite your lineage and gain new buffs.")
    async def clan_reroll(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})

        # 1. Verification
        if not player:
            return await interaction.response.send_message("❌ You must `/start` your journey first!", ephemeral=True)
        
        current_rerolls = player.get("clan_rerolls", 0)
        if current_rerolls <= 0:
            return await interaction.response.send_message("❌ No rerolls available. Check `/codes` or the shop!", ephemeral=True)

        # 2. Fetch Clan Registry
        all_clans = await db.clans.find().to_list(length=100)
        if not all_clans:
            return await interaction.response.send_message("❌ No clans found in the database. Contact an Admin.")

        # 3. Weighted Rarity Calculation
        # Higher roll_chance = more common. Lower = rarer (e.g., 0.01 for 1%).
        weights = [c.get('roll_chance', 0.1) for c in all_clans]
        chosen_clan = random.choices(all_clans, weights=weights, k=1)[0]

        # 4. Handle Stat Transition
        # We fetch the old clan buffs to subtract them, ensuring no infinite stat stacking
        old_clan_name = player.get("clan", "None")
        old_clan = await db.clans.find_one({"name": old_clan_name})
        
        old_hp = old_clan.get("hp_buff", 0) if old_clan else 0
        old_ce = old_clan.get("ce_buff", 0) if old_clan else 0
        old_dmg = old_clan.get("dmg_buff", 0) if old_clan else 0

        new_hp = chosen_clan.get("hp_buff", 0)
        new_ce = chosen_clan.get("ce_buff", 0)
        new_dmg = chosen_clan.get("dmg_buff", 0)

        # 5. Database Update (Atomic)
        await db.players.update_one(
            {"_id": user_id},
            {
                "$set": {"clan": chosen_clan['name']},
                "$inc": {
                    "clan_rerolls": -1,
                    "stats.max_hp": new_hp - old_hp,
                    "stats.max_ce": new_ce - old_ce,
                    "stats.dmg": new_dmg - old_dmg,
                    # Auto-heal the player for the difference
                    "stats.current_hp": new_hp - old_hp,
                    "stats.current_ce": new_ce - old_ce
                }
            }
        )

        # 6. High-Quality Presentation
        rarity_color = 0x39FF14 # Default Neon Green
        chance = chosen_clan.get('roll_chance', 1)
        if chance <= 0.01: rarity_color = 0xe74c3c # Special Grade Red
        elif chance <= 0.05: rarity_color = 0xf1c40f # Gold

        embed = discord.Embed(
            title="🧬 LINEAGE MANIFESTATION",
            description=f"Your soul has been reshaped. You are now a member of the **{chosen_clan['name']}** clan.",
            color=rarity_color
        )
        
        embed.add_field(name="Inherited Traits", value=f"❤️ HP: `+{new_hp}`\n🧪 CE: `+{new_ce}`\n💥 DMG: `+{new_dmg}`", inline=True)
        embed.add_field(name="Rarity", value=f"`{chance * 100}% Chance`", inline=True)
        embed.set_footer(text=f"Rerolls Remaining: {current_rerolls - 1}")
        
        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(RerollCog(bot))
        
