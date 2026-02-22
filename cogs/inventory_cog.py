import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager

class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="inventory", description="Check your collection of Cursed Techniques, Tools, and Styles.")
    async def inventory(self, interaction: discord.Interaction):
        """Displays a categorized list of everything the player owns."""
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})

        if not player:
            return await interaction.response.send_message("❌ You haven't started your journey yet. Use `/start`!", ephemeral=True)

        inventory_list = player.get("inventory", [])
        loadout = player.get("loadout", {})

        embed = discord.Embed(
            title=f"🎒 ARCHIVE: {interaction.user.display_name}",
            color=0x3498db
        )

        if not inventory_list:
            embed.description = "🛡️ *Your inventory is empty. Purchase techniques in the shop or claim victory over bosses to fill your arsenal.*"
        else:
            # Categorizing for "Crazy Good Quality" feel
            # In a real scenario, you'd fetch item types from DB, 
            # but here we'll display the list cleanly.
            items_str = "\n".join([f"• **{item}**" for item in inventory_list])
            embed.add_field(name="📜 OWNED ASSETS", value=items_str, inline=False)

        # Show active loadout prominently
        current_loadout = (
            f"🌀 **CT:** `{loadout.get('technique', 'None')}`\n"
            f"⚔️ **Tool:** `{loadout.get('weapon', 'None')}`\n"
            f"👊 **Style:** `{loadout.get('fighting_style', 'None')}`"
        )
        embed.add_field(name="🥋 ACTIVE LOADOUT", value=current_loadout, inline=False)

        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="equip", description="Set a technique or weapon from your inventory as active.")
    @app_commands.choices(category=[
        app_commands.Choice(name="Cursed Technique", value="technique"),
        app_commands.Choice(name="Weapon", value="weapon"),
        app_commands.Choice(name="Fighting Style", value="fighting_style")
    ])
    async def equip(self, interaction: discord.Interaction, category: str, item_name: str):
        """Equips an item and validates ownership."""
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})

        if not player:
            return await interaction.response.send_message("❌ Profile not found.", ephemeral=True)

        inventory = player.get("inventory", [])
        
        # Validation: Check if the player actually owns the item
        # We use a case-insensitive check to be user-friendly
        owned_item = next((i for i in inventory if i.lower() == item_name.lower()), None)

        if not owned_item:
            return await interaction.response.send_message(
                f"❌ You do not own **{item_name}**. Check your `/inventory` for available options.", 
                ephemeral=True
            )

        # Update the loadout in the database
        await db.players.update_one(
            {"_id": user_id},
            {"$set": {f"loadout.{category}": owned_item}}
        )

        embed = discord.Embed(
            title="⚙️ LOADOUT UPDATED",
            description=f"Successfully synchronized **{owned_item}** to your **{category.replace('_', ' ')}** slot.",
            color=0x2ecc71
        )
        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(InventoryCog(bot))
        
