import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager

class WorldBossAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="wb_list", description="Admin: List all registered World Bosses.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_list(self, interaction: discord.Interaction):
        """Fetches all bosses from the DB and displays their primary stats."""
        # 1. Fetch all NPCs marked as world bosses
        boss_cursor = db.npcs.find({"is_world_boss": True})
        bosses = await boss_cursor.to_list(length=100)

        if not bosses:
            return await interaction.response.send_message("🌑 The database is empty. No Special Grades registered.", ephemeral=True)

        embed = discord.Embed(
            title="📖 SPECIAL GRADE ENCYCLOPEDIA",
            description="All registered World Boss entities currently in the database.",
            color=0x2b2d31
        )

        for boss in bosses:
            status = "🔴 ACTIVE" if boss.get("current_hp", 0) > 0 else "⚪ DORMANT"
            hp_val = f"{boss['max_hp']:,}"
            dmg_val = boss.get('base_dmg', 'N/A')
            
            embed.add_field(
                name=f"{boss['name']} [{status}]",
                value=f"**HP:** `{hp_val}`\n**Base DMG:** `{dmg_val}`",
                inline=True
            )

        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="wb_setup_channel", description="Set the raid channel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_setup_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await db.db["settings"].update_one({"setting": "wb_channel"}, {"$set": {"channel_id": channel.id}}, upsert=True)
        await interaction.response.send_message(f"✅ Raid channel set to {channel.mention}")

    @app_commands.command(name="wb_setup_role", description="Set the notification role.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_setup_role(self, interaction: discord.Interaction, role: discord.Role):
        await db.db["settings"].update_one({"setting": "wb_role"}, {"$set": {"role_id": role.id}}, upsert=True)
        await interaction.response.send_message(f"✅ Notification role set to **{role.name}**")

    @app_commands.command(name="wb_create", description="Register a Special Grade Boss.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_create(self, interaction: discord.Interaction, name: str, hp: int, base_dmg: int, image_url: str):
        boss_data = {
            "name": name, "max_hp": hp, "current_hp": 0,
            "base_dmg": base_dmg, "image": image_url, "is_world_boss": True, "phase": 1
        }
        await db.npcs.update_one({"name": name}, {"$set": boss_data}, upsert=True)
        await interaction.response.send_message(f"📜 **{name}** registered with `{hp:,}` HP.")

    @app_commands.command(name="wb_skills", description="Assign techniques to the boss.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_skills(self, interaction: discord.Interaction, name: str, technique: str, weapon: str, style: str):
        await db.npcs.update_one({"name": name}, {"$set": {"technique": technique, "weapon": weapon, "fighting_style": style}})
        await interaction.response.send_message(f"⚔️ {name} skills updated.")

    @app_commands.command(name="wb_start", description="Force start a Boss event.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_start(self, interaction: discord.Interaction, name: str):
        boss = await db.npcs.find_one({"name": name, "is_world_boss": True})
        if not boss: return await interaction.response.send_message("❌ Boss not found.")
        
        # Reset to Phase 1 and Max HP
        await db.npcs.update_one({"name": name}, {"$set": {"current_hp": boss["max_hp"], "phase": 1}})
        await interaction.response.send_message(f"🚨 **{name}** has manifested! React to its presence with `!CE`, `!F`, or `!W`.")

async def setup(bot):
    await bot.add_cog(WorldBossAdminCog(bot))
        
