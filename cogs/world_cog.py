import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
import asyncio
import random

class WorldCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Mapping rarity to visual emojis for the shop
        self.rarity_icons = {
            "Common": "⚪", "Rare": "🔵", "Epic": "🟣", 
            "Legendary": "🟡", "Special Grade": "🔴"
        }

    # --- MARKETPLACE & SHOP ---
    @app_commands.command(name="technique_shop", description="View currently stocked techniques in the Jujutsu Market.")
    async def tech_shop(self, interaction: discord.Interaction):
        """Displays all available techniques with their Rarity and Price."""
        # Fetching all techniques currently in the market
        cursor = db.techniques.find({})
        stock = await cursor.to_list(length=100)
        
        if not stock:
            return await interaction.response.send_message("🏪 The shop is currently empty. Check back later!", ephemeral=True)
            
        embed = discord.Embed(
            title="🏪 CURSED TECHNIQUE MARKET", 
            description="Invest your Yen into powerful Cursed Techniques.",
            color=0x3498db
        )
        
        for tech in stock:
            rarity = tech.get("rarity", "Common")
            icon = self.rarity_icons.get(rarity, "⚪")
            price = tech.get("price", 0)
            
            embed.add_field(
                name=f"{icon} {tech['name']}", 
                value=f"**Grade:** {rarity}\n**Price:** ¥{price:,}", 
                inline=True
            )
            
        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Purchase a technique from the shop.")
    async def buy(self, interaction: discord.Interaction, technique_name: str):
        """Syncs purchase with the new Inventory system."""
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})
        tech = await db.techniques.find_one({"name": technique_name})
        
        if not player:
            return await interaction.response.send_message("❌ You need to create a profile first!", ephemeral=True)
        if not tech: 
            return await interaction.response.send_message("❌ This technique is not currently in stock.", ephemeral=True)
            
        # Check if they already own it
        if technique_name in player.get("inventory", []):
            return await interaction.response.send_message(f"❌ You already own **{technique_name}**!", ephemeral=True)

        player_money = player.get("money", 0)
        tech_price = tech.get("price", 0)

        if player_money < tech_price:
            return await interaction.response.send_message(f"❌ Insufficient Yen! You need ¥{tech_price - player_money:,} more.", ephemeral=True)

        # UPDATED LOGIC: Update money AND the new 'inventory' field
        await db.players.update_one(
            {"_id": user_id},
            {
                "$inc": {"money": -tech_price}, 
                "$addToSet": {"inventory": technique_name} # THIS FIXES THE EMPTY INVENTORY ISSUE
            }
        )

        embed = discord.Embed(
            title="📜 PURCHASE SUCCESSFUL",
            description=f"You have acquired the **{technique_name}**!\n\nUse `/equip` to set this as your active Cursed Technique.",
            color=0x2ecc71
        )
        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

    # --- RAID SYSTEM ---
    @app_commands.command(name="raid_create", description="Admin: Setup a Raid encounter.")
    async def raid_create(self, interaction: discord.Interaction, name: str, boss: str, drop: str, chance: float):
        raid_data = {
            "name": name, "boss": boss, "drop": drop, "chance": chance,
            "players": [], "host_id": str(interaction.user.id), "status": "Lobby"
        }
        await db.raids.update_one({"name": name}, {"$set": raid_data}, upsert=True)
        
        embed = discord.Embed(
            title="🚨 RAID NOTIFICATION",
            description=f"A new raid **{name}** has been hosted!\n**Boss:** {boss}\n**Potential Drop:** {drop}",
            color=0xf1c40f
        )
        BannerManager.apply(embed, type="combat")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="raid_join", description="Join an active raid lobby.")
    async def raid_join(self, interaction: discord.Interaction, name: str):
        raid = await db.raids.find_one({"name": name})
        if not raid: return await interaction.response.send_message("❌ Raid lobby not found.", ephemeral=True)
        
        await db.raids.update_one({"name": name}, {"$addToSet": {"players": str(interaction.user.id)}})
        await interaction.response.send_message(f"✅ {interaction.user.display_name} has entered the raid lobby.")

    # --- NPC MANAGEMENT ---
    @app_commands.command(name="npc_list", description="List all standard registered manifestations.")
    async def npc_list(self, interaction: discord.Interaction):
        npcs = await db.npcs.find({"is_world_boss": False}).to_list(100)
        if not npcs:
            return await interaction.response.send_message("🌑 No standard NPCs found.")
            
        names = [f"• {n['name']} (HP: {n.get('hp', '???')})" for n in npcs]
        
        embed = discord.Embed(title="👹 REGISTERED CURSES", description="\n".join(names), color=0x2b2d31)
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(WorldCog(bot))
        
