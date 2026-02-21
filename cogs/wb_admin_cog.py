import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager

class WorldBossAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="wb_setup_channel", description="Set the raid channel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_setup_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await db.db["settings"].update_one({"setting": "wb_channel"}, {"$set": {"channel_id": channel.id}}, upsert=True)
        await interaction.response.send_message(f"✅ Raid channel set to {channel.mention}")

    @app_commands.command(name="wb_setup_role", description="Set the role to be pinged for World Bosses.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_setup_role(self, interaction: discord.Interaction, role: discord.Role):
        await db.db["settings"].update_one({"setting": "wb_role"}, {"$set": {"role_id": role.id}}, upsert=True)
        await interaction.response.send_message(f"✅ Notification role set to **{role.name}**")

    @app_commands.command(name="wb_create", description="Register a Special Grade Boss.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_create(self, interaction: discord.Interaction, name: str, hp: int, base_dmg: int, image_url: str):
        boss_data = {
            "name": name, "max_hp": hp, "current_hp": 0,
            "base_dmg": base_dmg, "image": image_url, "is_world_boss": True
        }
        await db.npcs.update_one({"name": name}, {"$set": boss_data}, upsert=True)
        await interaction.response.send_message(f"📜 **{name}** registered with `{hp:,}` HP.")

    @app_commands.command(name="wb_skills", description="Assign techniques to the boss.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_skills(self, interaction: discord.Interaction, name: str, technique: str, weapon: str, style: str):
        await db.npcs.update_one({"name": name}, {"$set": {"technique": technique, "weapon": weapon, "fighting_style": style}})
        await interaction.response.send_message(f"⚔️ {name} skills updated.")

    @app_commands.command(name="wb_start", description="Force start a Boss event and AOE loop.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_start(self, interaction: discord.Interaction, name: str):
        boss = await db.npcs.find_one({"name": name, "is_world_boss": True})
        if not boss: return await interaction.response.send_message("❌ Boss not found.")
        
        await db.npcs.update_one({"name": name}, {"$set": {"current_hp": boss["max_hp"]}})
        
        combat_cog = self.bot.get_cog("WorldBossCog")
        if combat_cog:
            self.bot.loop.create_task(combat_cog.boss_attack_loop(interaction.channel, name))
            await interaction.response.send_message(f"🚨 **{name}** has manifested! AOE loop started.")
        else:
            await interaction.response.send_message("❌ WorldBossCog not loaded.")

    @app_commands.command(name="wb_ping", description="Ping the notification role.")
    @app_commands.checks.has_permissions(administrator=True)
    async def wb_ping(self, interaction: discord.Interaction):
        config_chan = await db.db["settings"].find_one({"setting": "wb_channel"})
        config_role = await db.db["settings"].find_one({"setting": "wb_role"})
        if not config_chan: return await interaction.response.send_message("❌ Setup channel first.")
        
        channel = self.bot.get_channel(config_chan.get("channel_id"))
        role_ping = f"<@&{config_role['role_id']}>" if config_role else "@everyone"
        
        embed = discord.Embed(title="📢 SPECIAL GRADE ALERT", description="All sorcerers report to the raid channel!", color=0xF1C40F)
        BannerManager.apply(embed, type="main")
        await channel.send(content=role_ping, embed=embed)
        await interaction.response.send_message("✅ Ping sent.")

async def setup(bot):
    await bot.add_cog(WorldBossAdminCog(bot))
                                                           
