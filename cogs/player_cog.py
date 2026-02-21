import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from database.models import player_model
from utils.embeds import JJKEmbeds
from utils.checks import not_in_combat
import random

class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="start", description="Begin your journey as a Sorcerer.")
    async def start(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        exists = await db.players.find_one({"_id": user_id})
        if exists:
            return await interaction.response.send_message("❌ You already have a profile!", ephemeral=True)
        
        new_player = player_model(user_id, interaction.user.name)
        await db.players.insert_one(new_player)
        await interaction.response.send_message("⛩️ Welcome to the Tokyo Jujutsu High. Use `/profile` to see your stats.")

    @app_commands.command(name="profile", description="View your stats, grade, and money.")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        data = await db.players.find_one({"_id": str(target.id)})
        if not data:
            return await interaction.response.send_message("❌ No profile found.", ephemeral=True)
        
        embed = JJKEmbeds.profile(data)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="upgrade_stats", description="Use stat points to buff CE, DMG, or HP.")
    @not_in_combat()
    async def upgrade_stats(self, interaction: discord.Interaction, stat: str, amount: int):
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})
        
        if player["stat_points"] < amount:
            return await interaction.response.send_message("❌ Not enough stat points!", ephemeral=True)

        stat_map = {
            "hp": "stats.max_hp",
            "ce": "stats.max_ce",
            "dmg": "stats.dmg"
        }
        
        target_stat = stat_map.get(stat.lower())
        if not target_stat:
            return await interaction.response.send_message("❌ Choose: hp, ce, or dmg.", ephemeral=True)

        # Scale HP/CE by 10 per point, DMG by 2 per point
        multiplier = 10 if stat.lower() in ["hp", "ce"] else 2
        inc_val = amount * multiplier

        await db.players.update_one(
            {"_id": user_id},
            {"$inc": {target_stat: inc_val, "stat_points": -amount}}
        )
        await interaction.response.send_message(f"📈 Upgraded **{stat.upper()}** by **{inc_val}**!")

    @app_commands.command(name="inventory", description="Show your items, weapons, and techniques.")
    async def inventory(self, interaction: discord.Interaction):
        player = await db.players.find_one({"_id": str(interaction.user.id)})
        inv = player.get("inventory", [])
        techs = player.get("techniques", [])
        
        embed = discord.Embed(title=f"🎒 {interaction.user.name}'s Inventory", color=0x2f3136)
        embed.add_field(name="📜 Techniques", value=", ".join(techs) if techs else "None", inline=False)
        embed.add_field(name="⚔️ Items/Weapons", value=", ".join(inv) if inv else "None", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="equip", description="Equip a Technique, Weapon, or Fighting Style.")
    @not_in_combat()
    async def equip(self, interaction: discord.Interaction, category: str, name: str):
        # Category: technique, weapon, fighting_style
        cat = category.lower()
        player = await db.players.find_one({"_id": str(interaction.user.id)})
        
        # Check if they own it
        owned = False
        if cat == "technique" and name in player.get("techniques", []): owned = True
        elif name in player.get("inventory", []): owned = True
        
        if not owned:
            return await interaction.response.send_message(f"❌ You do not own the {cat}: {name}", ephemeral=True)

        await db.players.update_one(
            {"_id": str(interaction.user.id)},
            {"$set": {f"loadout.{cat}": name}}
        )
        await interaction.response.send_message(f"✅ Equipped **{name}** as your **{cat}**.")

    @app_commands.command(name="use_code", description="Redeem a code for rerolls or items.")
    async def use_code(self, interaction: discord.Interaction, code_name: str):
        code = await db.codes.find_one({"name": code_name})
        user_id = str(interaction.user.id)
        
        if not code:
            return await interaction.response.send_message("❌ Invalid code.", ephemeral=True)
        if user_id in code.get("users", []):
            return await interaction.response.send_message("❌ Code already used.", ephemeral=True)

        await db.players.update_one({"_id": user_id}, {"$inc": {"clan_rerolls": code["rerolls"]}})
        await db.codes.update_one({"name": code_name}, {"$push": {"users": user_id}})
        await interaction.response.send_message(f"🎟️ Code redeemed! Gained **{code['rerolls']}** Clan Rerolls.")

async def setup(bot):
    await bot.add_cog(PlayerCog(bot))
                    
