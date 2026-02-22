import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
from utils.checks import is_admin

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- CLAN SYSTEM ---
    @app_commands.command(name="clan_create", description="Admin: Create a Clan with specific buffs.")
    @is_admin()
    async def clan_create(self, interaction: discord.Interaction, name: str, hp_buff: int, ce_buff: int, dmg_buff: int, roll_chance: float):
        clan_data = {
            "name": name, 
            "hp_buff": hp_buff, 
            "ce_buff": ce_buff, 
            "dmg_buff": dmg_buff, 
            "roll_chance": roll_chance
        }
        await db.clans.update_one({"name": name}, {"$set": clan_data}, upsert=True)
        
        embed = discord.Embed(title="⛩️ CLAN REGISTERED", description=f"**{name}** has been added to the lineage database.", color=0x2ecc71)
        embed.add_field(name="Buffs", value=f"HP: +{hp_buff} | CE: +{ce_buff} | DMG: +{dmg_buff}")
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    # --- ITEM & WEAPON SYSTEM ---
    @app_commands.command(name="item_create", description="Admin: Create a Weapon or Accessory.")
    @app_commands.choices(rarity=[
        app_commands.Choice(name="Common", value="Common"),
        app_commands.Choice(name="Rare", value="Rare"),
        app_commands.Choice(name="Epic", value="Epic"),
        app_commands.Choice(name="Legendary", value="Legendary"),
        app_commands.Choice(name="Special Grade", value="Special Grade")
    ])
    async def item_create(self, interaction: discord.Interaction, name: str, is_weapon: bool, rarity: str, damage: int = 0):
        # Items now use the Rarity system for consistent visuals
        item_data = {
            "name": name, 
            "is_weapon": is_weapon, 
            "damage": damage, 
            "rarity": rarity
        }
        await db.items.update_one({"name": name}, {"$set": item_data}, upsert=True)
        
        embed = discord.Embed(title="📦 ITEM FORGED", description=f"**{name}** is now available in the world.", color=0x3498db)
        embed.add_field(name="Stats", value=f"Type: {'Weapon' if is_weapon else 'Accessory'}\nGrade: {rarity}\nDMG: {damage}")
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    # --- TECHNIQUE & SKILL SYSTEM ---
    @app_commands.command(name="technique_create", description="Admin: Register a Technique and its market price.")
    async def tech_create(self, interaction: discord.Interaction, name: str, stock_chance: float, price: int, rarity: str):
        tech_data = {
            "name": name, 
            "stock_chance": stock_chance, 
            "price": price, 
            "rarity": rarity
        }
        await db.techniques.update_one({"name": name}, {"$set": tech_data}, upsert=True)
        
        embed = discord.Embed(title="📜 TECHNIQUE DOCUMENTED", description=f"**{name}** added to the Jujutsu archives.", color=0x9b59b6)
        embed.add_field(name="Market Info", value=f"Price: ¥{price:,}\nStock Chance: {stock_chance*100}%")
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="technique_skills", description="Admin: Map move names and damage to !CE slots.")
    async def tech_skills(self, interaction: discord.Interaction, tech_name: str, 
                         s1_name: str, s1_dmg: int, 
                         s2_name: str, s2_dmg: int, 
                         s3_name: str, s3_dmg: int):
        """Maps specific moves to the tech and creates entries in the skills collection."""
        # 1. Update the Technique record
        await db.techniques.update_one(
            {"name": tech_name},
            {"$set": {"skills_mapped": True}}
        )

        # 2. Create/Update Skill Move Entries for the combat engine to read
        moves = [
            {"move_number": 1, "name": tech_name, "move_title": s1_name, "damage": s1_dmg},
            {"move_number": 2, "name": tech_name, "move_title": s2_name, "damage": s2_dmg},
            {"move_number": 3, "name": tech_name, "move_title": s3_name, "damage": s3_dmg}
        ]
        
        for move in moves:
            await db.skills.update_one(
                {"name": move["name"], "move_number": move["move_number"]},
                {"$set": move},
                upsert=True
            )

        embed = discord.Embed(title="⚔️ SKILLS SYNCHRONIZED", description=f"Moves for **{tech_name}** are now combat-ready.", color=0xe74c3c)
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    # --- NPC & ECONOMY ---
    @app_commands.command(name="npc_create", description="Admin: Create a standard NPC (Not a World Boss).")
    async def npc_create(self, interaction: discord.Interaction, name: str, hp: int, dmg: int, image_url: str):
        npc_data = {
            "name": name, "is_world_boss": False, "hp": hp, "dmg": dmg, "image": image_url
        }
        await db.npcs.update_one({"name": name}, {"$set": npc_data}, upsert=True)
        await interaction.response.send_message(f"👹 NPC **{name}** registered.")

    @app_commands.command(name="codes_create", description="Admin: Create reward codes.")
    async def codes_create(self, interaction: discord.Interaction, name: str, rerolls: int, money: int = 0):
        await db.codes.insert_one({"name": name, "rerolls": rerolls, "money": money, "users": []})
        await interaction.response.send_message(f"🎟️ Code `{name}` created.")

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
                             
