import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
import random

class WorldBossAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Visual theme mapping for different threat levels
        self.boss_rarities = {
            "Common": 0x95a5a6,
            "Rare": 0x3498db,
            "Epic": 0x9b59b6,
            "Legendary": 0xf1c40f,
            "Special Grade": 0xe74c3c
        }

    # --- SETUP COMMANDS ---

    @app_commands.command(name="wb_spawn_multi", description="Admin: Set up to 6 authorized raid channels.")
    @app_commands.describe(
        c1="Channel 1", c2="Channel 2", c3="Channel 3", 
        c4="Channel 4", c5="Channel 5", c6="Channel 6"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_spawn_multi(self, interaction: discord.Interaction, 
                               c1: discord.TextChannel, 
                               c2: discord.TextChannel = None, 
                               c3: discord.TextChannel = None, 
                               c4: discord.TextChannel = None, 
                               c5: discord.TextChannel = None, 
                               c6: discord.TextChannel = None):
        """Registers multiple channels for boss activity in the database."""
        channels = [c.id for c in [c1, c2, c3, c4, c5, c6] if c is not None]
        
        await db.db["settings"].update_one(
            {"setting": "wb_channels"},
            {"$set": {"channel_ids": channels}},
            upsert=True
        )
        
        channel_mentions = ", ".join([f"<#{cid}>" for cid in channels])
        embed = discord.Embed(
            title="⚙️ MULTI-CHANNEL CONFIG", 
            description=f"Authorized raid zones updated:\n{channel_mentions}", 
            color=0x2b2d31
        )
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="wb_setup_role", description="Admin: Set the role to be pinged for World Bosses.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_setup_role(self, interaction: discord.Interaction, role: discord.Role):
        """Saves the Role ID for targeted boss notifications."""
        await db.db["settings"].update_one(
            {"setting": "wb_role"},
            {"$set": {"role_id": role.id}},
            upsert=True
        )
        await interaction.response.send_message(f"✅ Notification role set to **{role.name}**.")

    # --- MANAGEMENT COMMANDS ---

    @app_commands.command(name="wb_create", description="Admin: Register a Special Grade Boss.")
    @app_commands.choices(rarity=[
        app_commands.Choice(name="Common", value="Common"),
        app_commands.Choice(name="Rare", value="Rare"),
        app_commands.Choice(name="Epic", value="Epic"),
        app_commands.Choice(name="Legendary", value="Legendary"),
        app_commands.Choice(name="Special Grade", value="Special Grade")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_create(self, interaction: discord.Interaction, name: str, hp: int, base_dmg: int, image_url: str, rarity: str):
        """Creates a boss entry with default parameters."""
        boss_data = {
            "name": name, 
            "max_hp": hp, 
            "current_hp": 0,
            "base_dmg": base_dmg, 
            "image": image_url, 
            "is_world_boss": True, 
            "phase": 1,
            "rarity": rarity,
            "domain_dmg": 500,
            "domain_max": 1,
            "domain_count": 0,
            "is_domain_active": False
        }
        await db.npcs.update_one({"name": name}, {"$set": boss_data}, upsert=True)
        
        embed = discord.Embed(
            title="👾 ENTITY REGISTERED",
            description=f"**{name}** added to database.\n**HP:** `{hp:,}`\n**Rarity:** `{rarity}`",
            color=self.boss_rarities.get(rarity, 0x2f3136)
        )
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="wb_start", description="Admin: Force a Boss to spawn immediately.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_start(self, interaction: discord.Interaction):
        """Manually triggers a boss manifestation across all sectors."""
        config_chans = await db.db["settings"].find_one({"setting": "wb_channels"})
        if not config_chans or not config_chans.get("channel_ids"):
            return await interaction.response.send_message("❌ No raid channels set.", ephemeral=True)

        active_boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})
        if active_boss:
            return await interaction.response.send_message(f"⚠️ **{active_boss['name']}** is already alive!", ephemeral=True)

        boss_cursor = db.npcs.find({"is_world_boss": True})
        all_bosses = await boss_cursor.to_list(length=100)
        if not all_bosses:
            return await interaction.response.send_message("❌ No bosses in database.", ephemeral=True)
        
        selected_boss = random.choice(all_bosses)
        
        # Reset boss status for fresh encounter
        await db.npcs.update_one(
            {"_id": selected_boss["_id"]},
            {"$set": {"current_hp": selected_boss["max_hp"], "phase": 1, "domain_count": 0, "is_domain_active": False}}
        )

        # Get ping role if configured
        role_data = await db.db["settings"].find_one({"setting": "wb_role"})
        ping_content = f"<@&{role_data['role_id']}>" if role_data else ""

        embed = discord.Embed(
            title=f"🚨 EMERGENCY MANIFESTATION: {selected_boss['name'].upper()}",
            description=f"The veil has been forcibly torn! **{selected_boss['name']}** has appeared!",
            color=self.boss_rarities.get(selected_boss.get('rarity'), 0xff0000)
        )
        if selected_boss.get("image"): embed.set_image(url=selected_boss["image"])
        BannerManager.apply(embed, type="combat")

        for channel_id in config_chans["channel_ids"]:
            channel = self.bot.get_channel(channel_id)
            if channel: await channel.send(content=ping_content, embed=embed)

        await interaction.response.send_message(f"✅ Spawned **{selected_boss['name']}**.", ephemeral=True)

    @app_commands.command(name="wb_despawn", description="Admin: Remove the current active World Boss.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_despawn(self, interaction: discord.Interaction):
        """Forcefully sets current boss HP to 0 and resets raid logic."""
        await db.npcs.update_many({"is_world_boss": True}, {"$set": {"current_hp": 0, "is_domain_active": False}})
        
        wb_cog = self.bot.get_cog("WorldBossCog")
        if wb_cog:
            if hasattr(wb_cog, 'aggro_list'): wb_cog.aggro_list.clear()
            if hasattr(wb_cog, 'is_boss_frozen'): wb_cog.is_boss_frozen = False

        await interaction.response.send_message("🧹 Raid cleared. All active entities returned to the shadows.")

    @app_commands.command(name="wb_list", description="Admin: View all registered World Bosses.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_list(self, interaction: discord.Interaction):
        bosses = await db.npcs.find({"is_world_boss": True}).to_list(length=100)
        if not bosses: return await interaction.response.send_message("🌑 No Bosses found.")

        embed = discord.Embed(title="📖 WORLD BOSS LIST", color=0x2b2d31)
        for boss in bosses:
            status = "🔴 LIVE" if boss.get("current_hp", 0) > 0 else "⚪ DORMANT"
            embed.add_field(
                name=boss['name'], 
                value=f"**Status:** {status}\n**HP:** `{boss['max_hp']:,}`\n**Rarity:** `{boss.get('rarity', 'Common')}`", 
                inline=True
            )
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(WorldBossAdminCog(bot))
                          
