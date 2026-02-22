import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
import random

class ClanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_clan_color(self, chance):
        """Assigns a visual tier based on how hard the clan is to roll."""
        if chance <= 0.01: return 0xe74c3c # Special Grade (Red)
        if chance <= 0.05: return 0xf1c40f # Legendary (Gold)
        if chance <= 0.15: return 0x9b59b6 # Epic (Purple)
        return 0x3498db # Common/Rare (Blue)

    @app_commands.command(name="roll_clan", description="Reroll your lineage to inherit powerful clan buffs.")
    async def roll_clan(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})

        if not player:
            return await interaction.response.send_message("❌ You must `/start` your journey first.", ephemeral=True)

        if player.get("clan_rerolls", 0) <= 0:
            return await interaction.response.send_message("❌ You have no Rerolls left!", ephemeral=True)

        all_clans = await db.clans.find().to_list(length=100)
        if not all_clans:
            return await interaction.response.send_message("❌ No clans found in the database.", ephemeral=True)

        # 1. Weighted Roll Logic
        weights = [c.get('roll_chance', 0.1) for c in all_clans]
        chosen_clan = random.choices(all_clans, weights=weights, k=1)[0]
        
        # 2. Buff Calculation (Subtraction of old, addition of new)
        old_clan_name = player.get("clan", "None")
        old_clan = await db.clans.find_one({"name": old_clan_name})
        
        old_hp = old_clan.get("hp_buff", 0) if old_clan else 0
        old_ce = old_clan.get("ce_buff", 0) if old_clan else 0
        old_dmg = old_clan.get("dmg_buff", 0) if old_clan else 0

        new_hp = chosen_clan.get("hp_buff", 0)
        new_ce = chosen_clan.get("ce_buff", 0)
        new_dmg = chosen_clan.get("dmg_buff", 0)

        # 3. Atomic Update: Swap buffs and deduct reroll
        # Note: 'ce' and 'max_hp' are the base stats, 'cur_ce' and 'current_hp' are the pools
        await db.players.update_one(
            {"_id": user_id},
            {
                "$set": {"clan": chosen_clan['name']},
                "$inc": {
                    "clan_rerolls": -1,
                    "stats.hp": new_hp - old_hp,
                    "stats.ce": new_ce - old_ce,
                    "stats.dmg": new_dmg - old_dmg,
                    "stats.current_hp": new_hp - old_hp,
                    "stats.cur_ce": new_ce - old_ce 
                }
            }
        )

        # 4. Presentation
        chance_percent = chosen_clan.get('roll_chance', 0) * 100
        embed = discord.Embed(
            title="🧬 LINEAGE MANIFESTED", 
            description=f"Your blood awakens. You have joined the **{chosen_clan['name']}** Clan!",
            color=self.get_clan_color(chosen_clan.get('roll_chance', 1))
        )
        
        embed.add_field(
            name="📊 Inheritance Buffs", 
            value=f"❤️ **HP:** `+{new_hp}`\n🧪 **CE:** `+{new_ce}`\n💥 **DMG:** `+{new_dmg}`",
            inline=True
        )
        embed.add_field(
            name="🍀 Rarity", 
            value=f"**{chance_percent}%** chance",
            inline=True
        )

        embed.set_footer(text=f"Rerolls remaining: {player.get('clan_rerolls', 1) - 1}")
        BannerManager.apply(embed, type="main")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ClanCog(bot))
