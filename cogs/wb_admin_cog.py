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

    @app_commands.command(name="wb_setup_channel", description="Admin: Set the raid channel for World Bosses.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_setup_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Sets the specific channel where boss spawns and pings occur."""
        await db.db["settings"].update_one(
            {"setting": "wb_channel"},
            {"$set": {"channel_id": channel.id}},
            upsert=True
        )
        embed = discord.Embed(
            title="⚙️ SYSTEM CONFIG", 
            description=f"Raid channel successfully set to: {channel.mention}", 
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

    @app_commands.command(name="wb_create", description="Admin: Register a Special Grade Boss with Rarity.")
    @app_commands.choices(rarity=[
        app_commands.Choice(name="Common", value="Common"),
        app_commands.Choice(name="Rare", value="Rare"),
        app_commands.Choice(name="Epic", value="Epic"),
        app_commands.Choice(name="Legendary", value="Legendary"),
        app_commands.Choice(name="Special Grade", value="Special Grade")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_create(self, interaction: discord.Interaction, name: str, hp: int, base_dmg: int, image_url: str, rarity: str):
        """Creates a boss entry with the specified stats and threat level."""
        boss_data = {
            "name": name, 
            "max_hp": hp, 
            "current_hp": 0,
            "base_dmg": base_dmg, 
            "image": image_url, 
            "is_world_boss": True, 
            "phase": 1,
            "rarity": rarity
        }
        await db.npcs.update_one({"name": name}, {"$set": boss_data}, upsert=True)
        
        embed = discord.Embed(
            title="👾 NEW ENTITY REGISTERED",
            description=f"**{name}** added to database.\n**Threat Level:** `{rarity}`\n**HP:** `{hp:,}`\n**Base ATK:** `{base_dmg}`",
            color=self.boss_rarities.get(rarity, 0x2f3136)
        )
        embed.set_thumbnail(url=image_url)
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="wb_skills", description="Admin: Assign combat techniques to a boss.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_skills(self, interaction: discord.Interaction, name: str, technique: str, weapon: str, style: str):
        """Sets the names of the attacks used in the Boss's retaliation."""
        await db.npcs.update_one(
            {"name": name}, 
            {"$set": {"technique": technique, "weapon": weapon, "fighting_style": style}}
        )
        await interaction.response.send_message(f"⚔️ **{name}** is now armed with `{technique}`, `{weapon}`, and `{style}`.")

    # --- NEW COOLDOWN COMMAND ---

    @app_commands.command(name="wb_cooldown", description="Admin: Set cooldowns for a skill set (Move 1-4).")
    @app_commands.describe(
        name="The name of the Technique/Weapon/Style",
        m1="Cooldown for Move 1 (seconds)",
        m2="Cooldown for Move 2 (seconds)",
        m3="Cooldown for Move 3 (seconds)",
        m4="Cooldown for Move 4 (seconds)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_cooldown(self, interaction: discord.Interaction, name: str, m1: int, m2: int, m3: int, m4: int):
        """Updates the cooldown values for all 4 moves of a specific skill in the database."""
        cds = [m1, m2, m3, m4]
        
        for i, cd in enumerate(cds, 1):
            await db.skills.update_one(
                {"name": name, "move_number": i},
                {"$set": {"cooldown": cd}}
            )

        embed = discord.Embed(
            title="⏳ COOLDOWN REGISTRY UPDATED",
            description=f"Standardized cooldowns applied to **{name}**.",
            color=0x34495e
        )
        for i, cd in enumerate(cds, 1):
            embed.add_field(name=f"Move {i}", value=f"`{cd}s`", inline=True)
        
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="wb_list", description="Admin: View all registered World Bosses.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_list(self, interaction: discord.Interaction):
        """Lists all bosses and their current dormant/active status."""
        boss_cursor = db.npcs.find({"is_world_boss": True})
        bosses = await boss_cursor.to_list(length=100)

        if not bosses:
            return await interaction.response.send_message("🌑 No Special Grades found in the database.", ephemeral=True)

        embed = discord.Embed(title="📖 SPECIAL GRADE ENCYCLOPEDIA", color=0x2b2d31)
        for boss in bosses:
            status = "🔴 ACTIVE" if boss.get("current_hp", 0) > 0 else "⚪ DORMANT"
            embed.add_field(
                name=f"{boss['name']} ({boss.get('rarity', 'Common')})",
                value=f"**Status:** {status}\n**Max HP:** `{boss['max_hp']:,}`",
                inline=True
            )
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="wb_ping", description="Admin: Ping the notification role in the raid channel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_ping(self, interaction: discord.Interaction):
        """Dispatches a notification to the raid role in the setup channel."""
        config_chan = await db.db["settings"].find_one({"setting": "wb_channel"})
        config_role = await db.db["settings"].find_one({"setting": "wb_role"})
        
        if not config_chan: 
            return await interaction.response.send_message("❌ Setup failed. Use `/wb_setup_channel` first.", ephemeral=True)
        
        channel = self.bot.get_channel(config_chan.get("channel_id"))
        if not channel:
            return await interaction.response.send_message("❌ Specified raid channel no longer exists.", ephemeral=True)

        role_ping = f"<@&{config_role['role_id']}>" if config_role else "@everyone"
        
        embed = discord.Embed(
            title="📢 RAID CALL TO ARMS", 
            description="A Special Grade threat has been spotted! Report to the raid channel immediately!", 
            color=0xF1C40F
        )
        BannerManager.apply(embed, type="main")
        
        await channel.send(content=role_ping, embed=embed)
        await interaction.response.send_message("✅ Raid alert dispatched!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(WorldBossAdminCog(bot))
    
