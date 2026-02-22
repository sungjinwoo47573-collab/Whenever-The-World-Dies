import discord
from discord import app_commands
from discord.ext import commands
import random
from database.connection import techniques_col, clans_col, players_col, codes_col
from config import create_embed, SUCCESS_COLOR, MAIN_COLOR

class Customization(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clan_create", description="Admin: Create a new Clan with buffs")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def clan_create(self, interaction: discord.Interaction, name: str, hp: int, dmg: int, stm: int, ce: int):
        clan_data = {
            "name": name,
            "hp_buff": hp,
            "dmg_buff": dmg,
            "stm_buff": stm,
            "ce_buff": ce
        }
        await clans_col.update_one({"name": name}, {"$set": clan_data}, upsert=True)
        await interaction.response.send_message(f"Clan **{name}** created with professional buffs.")

    @app_commands.command(name="clanreroll", description="Reroll your clan for better buffs")
    async def clan_reroll(self, interaction: discord.Interaction):
        player = await players_col.find_one({"user_id": interaction.user.id})
        if not player or player.get("money", 0) < 5000:
            return await interaction.response.send_message("You need ¥5,000 to reroll your lineage.", ephemeral=True)

        all_clans = await clans_col.find().to_list(length=100)
        if not all_clans:
            return await interaction.response.send_message("No clans found in the world.")

        new_clan = random.choice(all_clans)
        
        await players_col.update_one(
            {"user_id": interaction.user.id},
            {
                "$set": {
                    "clan": new_clan["name"],
                    "hp_buff": new_clan["hp_buff"],
                    "dmg_buff": new_clan["dmg_buff"],
                    "stm_buff": new_clan["stm_buff"],
                    "ce_buff": new_clan["ce_buff"]
                },
                "$inc": {"money": -5000}
            }
        )

        embed = create_embed(
            "🧬 Lineage Reroll", 
            f"Your bloodline has shifted...\nYou are now a member of the **{new_clan['name']}** Clan!",
            color=SUCCESS_COLOR
        )
        embed.add_field(name="Buffs", value=f"❤️ HP: +{new_clan['hp_buff']}\n💥 DMG: +{new_clan['dmg_buff']}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ctshop", description="Browse available Cursed Techniques")
    async def ct_shop(self, interaction: discord.Interaction):
        cts = await techniques_col.find().to_list(length=20)
        if not cts:
            return await interaction.response.send_message("The shop is currently empty.")

        embed = create_embed("🔥 Cursed Technique Shop", "Select a technique to purchase with Yen.")
        for ct in cts:
            embed.add_field(
                name=f"{ct['name']} ({ct['grade']})", 
                value=f"Price: ¥{ct['price']}\nStock: {ct.get('stock_chance', 100)}%", 
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="createcodes", description="Admin: Create reward codes")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def create_code(self, interaction: discord.Interaction, name: str, rerolls: int):
        await codes_col.insert_one({"code": name, "rerolls": rerolls, "used_by": []})
        await interaction.response.send_message(f"Code `{name}` created for {rerolls} rerolls!")

    @app_commands.command(name="redeemcodes", description="Redeem a reward code")
    async def redeem_code(self, interaction: discord.Interaction, code: str):
        code_data = await codes_col.find_one({"code": code})
        if not code_data:
            return await interaction.response.send_message("Invalid Code.", ephemeral=True)
        
        if interaction.user.id in code_data["used_by"]:
            return await interaction.response.send_message("You already used this code.", ephemeral=True)

        await players_col.update_one(
            {"user_id": interaction.user.id},
            {"$inc": {"money": 1000}} # Example reward
        )
        await codes_col.update_one({"code": code}, {"$push": {"used_by": interaction.user.id}})
        
        await interaction.response.send_message(f"Code `{code}` redeemed! You received rewards.")

async def setup(bot):
    await bot.add_cog(Customization(bot))
