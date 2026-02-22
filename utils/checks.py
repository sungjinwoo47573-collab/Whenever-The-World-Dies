import discord
from discord import app_commands
from database.connection import db

def has_profile():
    """Ensures the player exists in the database before running a command."""
    async def predicate(interaction: discord.Interaction) -> bool:
        player = await db.players.find_one({"_id": str(interaction.user.id)})
        if not player:
            await interaction.response.send_message(
                "❌ You haven't manifested your cursed energy yet! Use `/start` to begin your journey.", 
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)

def is_admin():
    """Restricts commands to server administrators."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "🚫 Restricted: You do not have the clearance (Admin) to use this technique.", 
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)

def not_in_combat():
    """Prevents actions that would disrupt an active combat encounter."""
    async def predicate(interaction: discord.Interaction) -> bool:
        player = await db.players.find_one({"_id": str(interaction.user.id)})
        if player and player.get("status") == "combat":
            await interaction.response.send_message(
                "⚠️ You are currently in the middle of a battle! Focus on your opponent.", 
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)
    
