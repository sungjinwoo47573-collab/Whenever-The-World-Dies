import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from database.models import clan_model, item_model, technique_model, npc_model
from utils.checks import is_admin

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- CLAN SYSTEM ---
    @app_commands.command(name="clan_create", description="Create a Clan with specific buffs.")
    @is_admin()
    async def clan_create(self, interaction: discord.Interaction, name: str, hp_buff: int, ce_buff: int, dmg_buff: int, roll_chance: float):
        new_clan = clan_model(name, hp_buff, ce_buff, dmg_buff, roll_chance)
        await db.clans.insert_one(new_clan)
        await interaction.response.send_message(f"⛩️ Clan **{name}** registered with {roll_chance*100}% roll rate.")

    @app_commands.command(name="clan_remove")
    @is_admin()
    async def clan_remove(self, interaction: discord.Interaction, name: str):
        await db.clans.delete_one({"name": name})
        await interaction.response.send_message(f"🗑️ Clan {name} removed.")

    # --- ITEM & WEAPON SYSTEM ---
    @app_commands.command(name="item_create", description="Create a Weapon or Accessory.")
    @is_admin()
    async def item_create(self, interaction: discord.Interaction, name: str, is_weapon: bool, damage: int = 0, grade: str = "Grade 4"):
        new_item = item_model(name, is_weapon, damage, grade)
        await db.items.insert_one(new_item)
        await interaction.response.send_message(f"📦 Item **{name}** (Weapon: {is_weapon}) created.")

    # --- TECHNIQUE SYSTEM ---
    @app_commands.command(name="technique_create", description="Register a Technique and its stock chance.")
    @is_admin()
    async def tech_create(self, interaction: discord.Interaction, name: str, stock_chance: float, price: int):
        new_tech = technique_model(name, stock_chance, price)
        await db.techniques.insert_one(new_tech)
        await interaction.response.send_message(f"📜 Technique **{name}** added to market database.")

    @app_commands.command(name="technique_skills", description="Map names to !CE1-5 slots.")
    @is_admin()
    async def tech_skills(self, interaction: discord.Interaction, tech_name: str, s1: str, s2: str, s3: str, s4: str, s5: str):
        await db.techniques.update_one(
            {"name": tech_name},
            {"$set": {"skills": {"1": s1, "2": s2, "3": s3, "4": s4, "5": s5}}}
        )
        await interaction.response.send_message(f"⚔️ Skills mapped for {tech_name}.")

    # --- NPC & SPAWNING ---
    @app_commands.command(name="npc_create", description="Create NPC with Image and Drop logic.")
    @is_admin()
    async def npc_create(self, interaction: discord.Interaction, name: str, is_boss: bool, hp: int, dmg: int, image_url: str):
        new_npc = npc_model(name, is_boss, hp, dmg, image_url)
        await db.npcs.insert_one(new_npc)
        await interaction.response.send_message(f"👹 NPC **{name}** registered.", ephemeral=False)

    @app_commands.command(name="npc_spawn_channel")
    @is_admin()
    async def npc_spawn_channel(self, interaction: discord.Interaction, npc_name: str, channel: discord.TextChannel):
        await db.npcs.update_one({"name": npc_name}, {"$addToSet": {"spawn_channels": channel.id}})
        await interaction.response.send_message(f"📍 {npc_name} will now manifest in {channel.mention}.")

    # --- CODES & ECONOMY ---
    @app_commands.command(name="codes_create")
    @is_admin()
    async def codes_create(self, interaction: discord.Interaction, name: str, rerolls: int):
        await db.codes.insert_one({"name": name, "rerolls": rerolls, "users": []})
        await interaction.response.send_message(f"🎟️ Code `{name}` created for {rerolls} rerolls.")

    @app_commands.command(name="set_money_drop")
    @is_admin()
    async def set_money(self, interaction: discord.Interaction, npc_name: str, amount: int):
        await db.npcs.update_one({"name": npc_name}, {"$set": {"money_drop": amount}})
        await interaction.response.send_message(f"💰 {npc_name} now drops ¥{amount}.")

    # --- BINDING VOWS ---
    @app_commands.command(name="binding_vow_create")
    @is_admin()
    async def bv_create(self, interaction: discord.Interaction, name: str, buff: str):
        # Buff stored as text to be parsed by combat engine
        await db.guild_config.update_one(
            {"_id": "vows"},
            {"$set": {name: buff}},
            upsert=True
        )
        await interaction.response.send_message(f"📜 Binding Vow **{name}** ({buff}) is now active in the world.")

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
    
