import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager

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
        await interaction.response.send_message(f"✅ Notification role set to **{role.name}**. Use `/wb_ping` to alert them!")

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
        """Creates a boss entry with Domain default parameters."""
        boss_data = {
            "name": name, 
            "max_hp": hp, 
            "current_hp": 0,
            "base_dmg": base_dmg, 
            "image": image_url, 
            "is_world_boss": True, 
            "phase": 1,
            "rarity": rarity,
            "domain_dmg": 500, # Default
            "domain_max": 1,   # Default
            "domain_count": 0,
            "is_domain_active": False
        }
        await db.npcs.update_one({"name": name}, {"$set": boss_data}, upsert=True)
        
        embed = discord.Embed(
            title="👾 ENTITY REGISTERED",
            description=f"**{name}** added to database.\n**Threat Level:** `{rarity}`\n**HP:** `{hp:,}`",
            color=self.boss_rarities.get(rarity, 0x2f3136)
        )
        embed.set_thumbnail(url=image_url)
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="wb_cooldown", description="Admin: Set cooldowns for a skill set (Move 1-4).")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_cooldown(self, interaction: discord.Interaction, name: str, m1: int, m2: int, m3: int, m4: int):
        """Updates move cooldowns in the database."""
        cds = [m1, m2, m3, m4]
        for i, cd in enumerate(cds, 1):
            await db.skills.update_one(
                {"name": name, "move_number": i},
                {"$set": {"cooldown": cd}}
            )
        await interaction.response.send_message(f"✅ Cooldowns for **{name}** updated: `{cds}`")

    @app_commands.command(name="wb_domain_set", description="Admin: Configure Boss Domain Expansion.")
    @app_commands.describe(name="Boss Name", damage="Total Domain DMG", max_use="Times it can use Domain")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_domain_set(self, interaction: discord.Interaction, name: str, damage: int, max_use: int = 1):
        """Sets the Domain Expansion parameters for a specific boss."""
        await db.npcs.update_one(
            {"name": name, "is_world_boss": True},
            {"$set": {"domain_dmg": damage, "domain_max": max_use}}
        )
        await interaction.response.send_message(f"✅ Domain set for **{name}**: `{damage} DMG`, Max `{max_use}` uses.")

    @app_commands.command(name="wb_ping", description="Admin: Alert all registered raid channels.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_ping(self, interaction: discord.Interaction):
        """Dispatches a notification to all authorized raid channels."""
        config_chans = await db.db["settings"].find_one({"setting": "wb_channels"})
        config_role = await db.db["settings"].find_one({"setting": "wb_role"})
        
        if not config_chans or not config_chans.get("channel_ids"): 
            return await interaction.response.send_message("❌ No channels set. Use `/wb_spawn_multi`.", ephemeral=True)
        
        role_ping = f"<@&{config_role['role_id']}>" if config_role else "@everyone"
        embed = discord.Embed(
            title="📢 GLOBAL RAID ALERT", 
            description="A Special Grade threat is moving across sectors! Report to raid zones!", 
            color=0xF1C40F
        )
        BannerManager.apply(embed, type="main")
        
        for channel_id in config_chans["channel_ids"]:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(content=role_ping, embed=embed)
        
        await interaction.response.send_message("✅ Raid alerts dispatched!", ephemeral=True)

    @app_commands.command(name="wb_list", description="Admin: View all registered World Bosses.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_list(self, interaction: discord.Interaction):
        boss_cursor = db.npcs.find({"is_world_boss": True})
        bosses = await boss_cursor.to_list(length=100)
        if not bosses:
            return await interaction.response.send_message("🌑 No Bosses found.", ephemeral=True)

        embed = discord.Embed(title="📖 SPECIAL GRADE ENCYCLOPEDIA", color=0x2b2d31)
        for boss in bosses:
            status = "🔴 ACTIVE" if boss.get("current_hp", 0) > 0 else "⚪ DORMANT"
            embed.add_field(name=boss['name'], value=f"Status: {status}\nMax HP: `{boss['max_hp']:,}`", inline=True)
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(WorldBossAdminCog(bot))
        
