import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from systems.economy import get_market_stock
from utils.embeds import JJKEmbeds
from utils.checks import is_admin

class WorldCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="raid_start", description="Create a temporary raid instance for a specific boss.")
    @is_admin()
    async def raid_start(self, interaction: discord.Interaction, boss_name: str):
        """Creates a private raid channel and pings the sorcerer role."""
        guild = interaction.guild
        
        # Fetch Boss data
        npc = await db.npcs.find_one({"name": boss_name})
        if not npc:
            return await interaction.response.send_message("❌ Boss not found in Registry.", ephemeral=True)

        # 1. Create a private category/channel for the raid
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }
        
        channel = await guild.create_text_channel(
            name=f"🏮-raid-{boss_name.replace(' ', '-').lower()}",
            overwrites=overwrites
        )

        # 2. Ping players and set the scene
        embed = JJKEmbeds.success(
            "RAID INITIATED",
            f"A high-level curse **{boss_name}** has manifested in {channel.mention}!\n"
            "Only the strongest sorcerers should enter. Type `!CE1` to engage."
        )
        embed.set_image(url=npc.get("image"))
        
        await interaction.response.send_message(f"🚨 Raid channel created: {channel.mention}")
        await channel.send(content="@everyone", embed=embed)

    @app_commands.command(name="shop", description="View the currently available Cursed Techniques and Items.")
    async def shop(self, interaction: discord.Interaction):
        """Displays a rotating selection of items using the economy system logic."""
        stock = await get_market_stock()
        
        if not stock:
            return await interaction.response.send_message("🏪 The market is currently empty. Check back later!")

        embed = discord.Embed(title="🏪 Jujutsu Marketplace", color=discord.Color.gold())
        
        for item in stock:
            embed.add_field(
                name=f"{item['name']} ({item['rarity']})",
                value=f"Price: ¥{item['buy_price']:,}\nID: `{item['_id']}`",
                inline=False
            )
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Purchase a technique from the shop.")
    async def buy(self, interaction: discord.Interaction, technique_name: str):
        """Deducts Yen and adds the technique to the player's inventory."""
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})
        tech = await db.techniques.find_one({"name": technique_name})

        if not tech or not player:
            return await interaction.response.send_message("❌ Transaction failed. Check your input.", ephemeral=True)

        if player["money"] < tech["buy_price"]:
            return await interaction.response.send_message("❌ You lack the Yen for this purchase.", ephemeral=True)

        # Update Database
        await db.players.update_one(
            {"_id": user_id},
            {
                "$inc": {"money": -tech["buy_price"]},
                "$push": {"inventory": tech["name"]}
            }
        )

        await interaction.response.send_message(
            embed=JJKEmbeds.success("Purchase Complete", f"You have acquired: **{technique_name}**!")
        )

async def setup(bot):
    await bot.add_cog(WorldCog(bot))
  
