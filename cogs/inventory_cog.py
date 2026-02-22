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
            embed.description = "🛡️ *Your inventory is empty. Purchase techniques in the shop or claim victory over bosses.*"
        else:
            # Categorization Logic: Fetching from respective collections to sort the view
            techs = []
            weapons = []
            styles = []

            for item in inventory_list:
                # Check Techniques
                if await db.techniques.find_one({"name": item}):
                    techs.append(item)
                # Check Weapons
                elif await db.items.find_one({"name": item, "is_weapon": True}):
                    weapons.append(item)
                # Check Styles
                elif await db.fighting_styles.find_one({"name": item}):
                    styles.append(item)
                else:
                    # Accessories or unmapped items
                    weapons.append(f"{item} (Misc)")

            if techs: embed.add_field(name="🌀 TECHNIQUES", value="\n".join([f"• {t}" for t in techs]), inline=True)
            if styles: embed.add_field(name="👊 STYLES", value="\n".join([f"• {s}" for s in styles]), inline=True)
            if weapons: embed.add_field(name="⚔️ TOOLS", value="\n".join([f"• {w}" for w in weapons]), inline=True)

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
        
        # Validation: Case-insensitive ownership check
        owned_item = next((i for i in inventory if i.lower() == item_name.lower()), None)

        if not owned_item:
            return await interaction.response.send_message(
                f"❌ You do not own **{item_name}**. Check your `/inventory`.", 
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
        
