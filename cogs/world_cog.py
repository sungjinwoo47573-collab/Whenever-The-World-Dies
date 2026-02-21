import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.embeds import JJKEmbeds
from utils.checks import handle_fatality
from systems.combat import npc_ai_loop, active_combats
import asyncio
import random

class WorldCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- RAID SYSTEM ---
    @app_commands.command(name="raid_create", description="Set up a Raid with a Boss and Drops.")
    async def raid_create(self, interaction: discord.Interaction, name: str, boss: str, drop: str, chance: float):
        raid_data = {
            "name": name,
            "boss": boss,
            "drop": drop,
            "chance": chance,
            "players": [],
            "host_id": str(interaction.user.id)
        }
        await db.raids.update_one({"name": name}, {"$set": raid_data}, upsert=True)
        embed = JJKEmbeds.raid_announcement(name, boss, None)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="raid_join")
    async def raid_join(self, interaction: discord.Interaction, name: str):
        raid = await db.raids.find_one({"name": name})
        if not raid: return await interaction.response.send_message("❌ Raid not found.")
        
        await db.raids.update_one({"name": name}, {"$addToSet": {"players": str(interaction.user.id)}})
        await interaction.response.send_message(f"✅ {interaction.user.display_name} joined the raid lobby.")

    @app_commands.command(name="raid_start")
    async def raid_start(self, interaction: discord.Interaction, name: str):
        raid = await db.raids.find_one({"name": name})
        if not raid or str(interaction.user.id) != raid["host_id"]:
            return await interaction.response.send_message("❌ Only the host can start the raid.")

        # Create Private Channel
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True)
        }
        
        player_list = []
        for p_id in raid["players"]:
            member = interaction.guild.get_member(int(p_id))
            if member:
                overwrites[member] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                player_list.append(member)

        raid_channel = await interaction.guild.create_text_channel(f"raid-{name}", overwrites=overwrites)
        
        # Spawn Boss
        boss_data = await db.npcs.find_one({"name": raid["boss"]})
        if not boss_data: return await raid_channel.send("❌ Boss data missing.")
        
        await raid_channel.send(f"⚠️ **THE VEIL IS DOWN.** {len(player_list)} sorcerers have entered.")
        await interaction.response.send_message(f"🚀 Raid started in {raid_channel.mention}!")
        
        # Start the AI Combat Loop
        ctx = await self.bot.get_context(await raid_channel.send(f"👹 **{boss_data['name']}** manifests!"))
        asyncio.create_task(npc_ai_loop(ctx, boss_data))

    # --- MARKETPLACE & SHOP ---
    @app_commands.command(name="technique_shop", description="View currently stocked techniques.")
    async def tech_shop(self, interaction: discord.Interaction):
        from systems.economy import get_technique_stock
        stock = await get_technique_stock()
        
        if not stock:
            return await interaction.response.send_message("🏪 The shop is currently empty. Check back later!")
            
        embed = discord.Embed(title="🏪 Cursed Technique Market", color=discord.Color.blue())
        for tech in stock:
            embed.add_field(name=tech["name"], value=f"Price: ¥{tech['price']:,}\nStock: Rare", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Purchase a technique from the shop.")
    async def buy(self, interaction: discord.Interaction, technique_name: str):
        player = await db.players.find_one({"_id": str(interaction.user.id)})
        tech = await db.techniques.find_one({"name": technique_name})
        
        if not tech: return await interaction.response.send_message("❌ Technique not found.")
        if player["money"] < tech["price"]:
            return await interaction.response.send_message("❌ Insufficient Yen!")

        await db.players.update_one(
            {"_id": str(interaction.user.id)},
            {"$inc": {"money": -tech["price"]}, "$addToSet": {"techniques": technique_name}}
        )
        await interaction.response.send_message(f"📜 You purchased **{technique_name}**!")

    # --- NPC MANAGEMENT ---
    @app_commands.command(name="npc_list")
    async def npc_list(self, interaction: discord.Interaction):
        npcs = await db.npcs.find().to_list(100)
        names = [f"• {n['name']} ({'Boss' if n['is_boss'] else 'Curse'})" for n in npcs]
        await interaction.response.send_message("**Registered Manifestations:**\n" + "\n".join(names))

async def setup(bot):
    await bot.add_cog(WorldCog(bot))
    
