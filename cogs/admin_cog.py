import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
from utils.checks import is_admin
import random

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rarity_colors = {
            "Common": 0x95a5a6, "Rare": 0x3498db, "Epic": 0x9b59b6, 
            "Legendary": 0xf1c40f, "Special Grade": 0xe74c3c
        }


    # --- ITEM & WEAPON SYSTEM ---
    @app_commands.command(name="item_create", description="Admin: Create a Weapon or Accessory.")
    @app_commands.choices(rarity=[
        app_commands.Choice(name="Common", value="Common"),
        app_commands.Choice(name="Rare", value="Rare"),
        app_commands.Choice(name="Epic", value="Epic"),
        app_commands.Choice(name="Legendary", value="Legendary"),
        app_commands.Choice(name="Special Grade", value="Special Grade")
    ])
    @is_admin()
    async def item_create(self, interaction: discord.Interaction, name: str, is_weapon: bool, rarity: str, damage: int = 0):
        item_data = {"name": name, "is_weapon": is_weapon, "damage": damage, "rarity": rarity}
        await db.items.update_one({"name": name}, {"$set": item_data}, upsert=True)
        
        embed = discord.Embed(title="📦 ITEM FORGED", description=f"**{name}** registered.", color=self.rarity_colors.get(rarity, 0x3498db))
        embed.add_field(name="Stats", value=f"Type: {'Weapon' if is_weapon else 'Accessory'}\nGrade: {rarity}\nDMG: {damage}")
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    # --- TECHNIQUE & SKILL SYSTEM ---
    @app_commands.command(name="technique_create", description="Admin: Register a Technique and its market price.")
    @is_admin()
    async def tech_create(self, interaction: discord.Interaction, name: str, stock_chance: float, price: int, rarity: str):
        tech_data = {"name": name, "stock_chance": stock_chance, "price": price, "rarity": rarity}
        await db.techniques.update_one({"name": name}, {"$set": tech_data}, upsert=True)
        
        embed = discord.Embed(title="📜 TECHNIQUE DOCUMENTED", description=f"**{name}** archived.", color=0x9b59b6)
        embed.add_field(name="Market Info", value=f"Price: ¥{price:,}\nStock: {stock_chance*100}%")
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="technique_skills", description="Admin: Map moves and cooldowns.")
    @is_admin()
    async def tech_skills(self, interaction: discord.Interaction, tech_name: str, 
                         s1_name: str, s1_dmg: int, s1_cd: int,
                         s2_name: str, s2_dmg: int, s2_cd: int,
                         s3_name: str, s3_dmg: int, s3_cd: int):
        moves = [
            {"move_number": 1, "name": tech_name, "move_title": s1_name, "damage": s1_dmg, "cooldown": s1_cd},
            {"move_number": 2, "name": tech_name, "move_title": s2_name, "damage": s2_dmg, "cooldown": s2_cd},
            {"move_number": 3, "name": tech_name, "move_title": s3_name, "damage": s3_dmg, "cooldown": s3_cd}
        ]
        for move in moves:
            await db.skills.update_one({"name": move["name"], "move_number": move["move_number"]}, {"$set": move}, upsert=True)

        await interaction.response.send_message(f"✅ Combat skills for **{tech_name}** synchronized.")

    # --- WORLD BOSS ADMINISTRATION ---
    @app_commands.command(name="wb_setup", description="Admin: Set raid channels and role.")
    @is_admin()
    async def wb_setup(self, interaction: discord.Interaction, role: discord.Role, c1: discord.TextChannel, c2: discord.TextChannel = None):
        channels = [c.id for c in [c1, c2] if c is not None]
        await db.db["settings"].update_one({"setting": "wb_config"}, {"$set": {"role_id": role.id, "channels": channels}}, upsert=True)
        await interaction.response.send_message("✅ World Boss raid configuration saved.")

    @app_commands.command(name="wb_create", description="Admin: Create a Special Grade World Boss.")
    @is_admin()
    async def wb_create(self, interaction: discord.Interaction, name: str, hp: int, dmg: int, image: str, rarity: str):
        boss_data = {
            "name": name, "max_hp": hp, "current_hp": 0, "base_dmg": dmg, "image": image,
            "is_world_boss": True, "rarity": rarity, "domain_dmg": 500, "domain_max": 1, "is_domain_active": False
        }
        await db.npcs.update_one({"name": name}, {"$set": boss_data}, upsert=True)
        await interaction.response.send_message(f"✅ World Boss **{name}** registered.")

    @app_commands.command(name="wb_start", description="Admin: Manually trigger a World Boss spawn.")
    @is_admin()
    async def wb_start(self, interaction: discord.Interaction):
        config = await db.db["settings"].find_one({"setting": "wb_config"})
        if not config: return await interaction.response.send_message("❌ Run `/wb_setup` first.")
        
        bosses = await db.npcs.find({"is_world_boss": True}).to_list(length=10)
        if not bosses: return await interaction.response.send_message("❌ No bosses created.")
        
        boss = random.choice(bosses)
        await db.npcs.update_one({"_id": boss["_id"]}, {"$set": {"current_hp": boss["max_hp"], "is_domain_active": False, "domain_count": 0}})
        
        embed = discord.Embed(title=f"🚨 EMERGENCY: {boss['name'].upper()}", description="A Special Grade threat has appeared!", color=0xff0000)
        embed.set_image(url=boss["image"])
        
        for cid in config["channels"]:
            chan = self.bot.get_channel(cid)
            if chan: await chan.send(content=f"<@&{config['role_id']}>", embed=embed)
        await interaction.response.send_message(f"✅ Spawned {boss['name']}.")

    # --- PLAYER MAINTENANCE & FIXES ---
    @app_commands.command(name="fix_player_ce", description="Admin: Restore a player's current CE to their Max CE.")
    @is_admin()
    async def fix_ce(self, interaction: discord.Interaction, member: discord.Member):
        player = await db.players.find_one({"_id": str(member.id)})
        if not player: return await interaction.response.send_message("❌ Player not found.")
        
        max_ce = player.get("stats", {}).get("ce", 100)
        await db.players.update_one({"_id": str(member.id)}, {"$set": {"stats.cur_ce": max_ce}})
        await interaction.response.send_message(f"✅ Restored {member.name}'s CE to `{max_ce}`.")

    @app_commands.command(name="codes_create", description="Admin: Create reward codes.")
    @is_admin()
    async def codes_create(self, interaction: discord.Interaction, name: str, rerolls: int, money: int = 0):
        await db.codes.insert_one({"name": name, "rerolls": rerolls, "money": money, "users": []})
        await interaction.response.send_message(f"🎟️ Code `{name}` created.")

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
        
