import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
from utils.checks import is_admin

class ClanAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clan_create", description="Admin: Register a new Clan into the database.")
    @is_admin()
    async def clan_create(
        self, 
        interaction: discord.Interaction, 
        name: str, 
        hp_buff: float, 
        ce_buff: float, 
        dmg_buff: float, 
        rarity: str,
        roll_chance: float
    ):
        """
        Creates a clan entry.
        Example: name="Gojo", hp_buff=1.2, ce_buff=2.0, dmg_buff=1.1, rarity="Legendary", roll_chance=0.01
        """
        clan_data = {
            "name": name,
            "hp_buff": hp_buff,   # 1.2 means +20% HP
            "ce_buff": ce_buff,   # 2.0 means double CE
            "dmg_buff": dmg_buff,
            "rarity": rarity,
            "roll_chance": roll_chance # 0.01 is 1%
        }

        # Save to the 'clans' collection
        await db.clans.update_one(
            {"name": name}, 
            {"$set": clan_data}, 
            upsert=True
        )

        embed = discord.Embed(
            title="Clan Registered",
            description=f"Successfully added the **{name}** clan to the archives.",
            color=0x2ecc71
        )
        embed.add_field(name="Rarity", value=rarity, inline=True)
        embed.add_field(name="Roll Chance", value=f"{roll_chance*100}%", inline=True)
        embed.add_field(name="Buffs", value=f"HP: x{hp_buff} | CE: x{ce_buff} | DMG: x{dmg_buff}", inline=False)
        
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clan_list", description="View all registered clans and their stats.")
    async def clan_list(self, interaction: discord.Interaction):
        """Public or Admin command to see available clans."""
        cursor = db.clans.find({})
        clans = await cursor.to_list(length=100)

        if not clans:
            return await interaction.response.send_message("No clans have been created yet.", ephemeral=True)

        embed = discord.Embed(title="⛩️ Available Lineages", color=0x3498db)
        
        for clan in clans:
            embed.add_field(
                name=f"{clan['name']} ({clan['rarity']})",
                value=f"Chance: {clan['roll_chance']*100}%\nBuffs: HP x{clan['hp_buff']}, CE x{clan['ce_buff']}",
                inline=True
            )

        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ClanAdminCog(bot))
                                                           
