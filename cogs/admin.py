import discord
from discord import app_commands
from discord.ext import commands
from database.connection import items_col, npcs_col, players_col
from config import create_embed, ADMIN_COLOR, SUCCESS_COLOR

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Helper check for Admin permissions (Change 'manage_guild' as needed)
    def is_admin():
        async def predicate(interaction: discord.Interaction):
            return interaction.user.guild_permissions.manage_guild
        return app_commands.check(predicate)

    @app_commands.command(name="itemcreate", description="Admin: Create a new item")
    @is_admin()
    async def item_create(self, interaction: discord.Interaction, name: str):
        await items_col.update_one({"name": name}, {"$set": {"name": name}}, upsert=True)
        await interaction.response.send_message(f"Item **{name}** created successfully.")

    @app_commands.command(name="npccreate", description="Admin: Create a Boss")
    @is_admin()
    async def npc_create(self, interaction: discord.Interaction, 
                         name: str, grade: str, raid: bool, 
                         drop_item: str, drop_chance: int, image_url: str, weapon_drop: str):
        npc_data = {
            "name": name,
            "grade": grade,
            "is_raid": raid,
            "drop": drop_item,
            "drop_chance": drop_chance,
            "image_url": image_url,
            "weapon_drop": weapon_drop,
            "hp_multiplier": 1.2 if raid else 1.0
        }
        await npcs_col.update_one({"name": name}, {"$set": npc_data}, upsert=True)
        await interaction.response.send_message(f"Boss **{name}** ({grade}) has been added to the database.")

    @app_commands.command(name="addmoney", description="Admin: Give money to a user")
    @is_admin()
    async def add_money(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        await players_col.update_one({"user_id": user.id}, {"$inc": {"money": amount}})
        await interaction.response.send_message(f"Granted ¥{amount} to {user.display_name}.")

    @app_commands.command(name="setlevel", description="Admin: Set user level")
    @is_admin()
    async def set_level(self, interaction: discord.Interaction, user: discord.Member, level: int):
        from database.models import get_grade_by_level
        grade = get_grade_by_level(level)
        await players_col.update_one(
            {"user_id": user.id}, 
            {"$set": {"level": level, "grade": grade}}
        )
        await interaction.response.send_message(f"Set {user.display_name}'s level to {level} ({grade}).")

    @app_commands.command(name="wipeeverythingfromdatabase", description="DANGER: Nuclear Wipe")
    @is_admin()
    async def wipe_db(self, interaction: discord.Interaction, confirm: str):
        if confirm == "YES":
            await players_col.delete_many({})
            await items_col.delete_many({})
            await npcs_col.delete_many({})
            embed = create_embed("☢️ DATABASE WIPED", "All player data, items, and NPCs have been erased.", color=ADMIN_COLOR)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Wipe cancelled. You must type 'YES' to confirm.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
      
