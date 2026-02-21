import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager

class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="inventory", description="View all your owned Techniques, Weapons, and Styles.")
    async def inventory(self, interaction: discord.Interaction):
        """Displays everything the player has collected."""
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})

        if not player:
            return await interaction.response.send_message("❌ You don't have a profile yet!", ephemeral=True)

        # Get the list of items from the database
        items = player.get("inventory", []) # Assuming 'inventory' is a list of strings
        
        if not items:
            desc = "Your inventory is currently empty. Visit the shop or defeat bosses to find gear!"
        else:
            # Sort items into categories for a cleaner look
            desc = "**Owned Items & Skills:**\n" + "\n".join([f"• {item}" for item in items])

        embed = discord.Embed(
            title=f"🎒 {interaction.user.name}'s Inventory",
            description=desc,
            color=0x3498db
        )
        
        # Show what is currently EQUIPPED at the bottom
        loadout = player.get("loadout", {})
        embed.add_field(
            name="Current Loadout", 
            value=f"🌀 **CT:** `{loadout.get('technique', 'None')}`\n"
                  f"⚔️ **Weapon:** `{loadout.get('weapon', 'None')}`\n"
                  f"👊 **Style:** `{loadout.get('fighting_style', 'None')}`",
            inline=False
        )

        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="equip", description="Equip an item from your inventory.")
    @app_commands.choices(category=[
        app_commands.Choice(name="Cursed Technique (CE)", value="technique"),
        app_commands.Choice(name="Weapon (W)", value="weapon"),
        app_commands.Choice(name="Fighting Style (F)", value="fighting_style")
    ])
    async def equip(self, interaction: discord.Interaction, category: str, item_name: str):
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})

        if not player: return await interaction.response.send_message("❌ No profile.")

        # Check if the player actually owns it
        if item_name not in player.get("inventory", []):
            return await interaction.response.send_message(f"❌ You don't own **{item_name}**!", ephemeral=True)

        # Update loadout
        await db.players.update_one(
            {"_id": user_id},
            {"$set": {f"loadout.{category}": item_name}}
        )

        await interaction.response.send_message(f"✅ Equipped **{item_name}** as your active {category}!")

async def setup(bot):
    await bot.add_cog(InventoryCog(bot))
      
