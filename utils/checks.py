import discord
from discord import app_commands
from database.connection import db

def is_admin():
    """Restricts command to users with Administrator permissions."""
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

def has_profile():
    """Ensures the player exists in the database before running commands."""
    async def predicate(interaction: discord.Interaction) -> bool:
        player = await db.players.find_one({"_id": str(interaction.user.id)})
        if not player:
            await interaction.response.send_message(
                "❌ Your soul has not yet manifested. Use `/start` to begin your journey.", 
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)

def not_in_combat():
    """Prevents inventory, stat, or clan changes during active channel combat."""
    async def predicate(interaction: discord.Interaction) -> bool:
        # Import inside function to avoid circular import issues
        from systems.combat import active_combats
        if interaction.channel_id in active_combats:
            await interaction.response.send_message(
                "❌ **CURSED LOCK:** Your focus is entirely on the enemy. You cannot manage your status now!", 
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)

async def handle_fatality(member: discord.Member, channel: discord.TextChannel):
    """
    The 'Permanent Loss' logic. When a player's HP hits 0, they are 
    temporarily removed from the channel to simulate being incapacitated.
    """
    try:
        # Reset permissions for the member in this specific channel
        await channel.set_permissions(member, overwrite=None)
        
        embed = discord.Embed(
            title="💀 CRITICAL DEFEAT",
            description=(
                f"Your presence has vanished from **{channel.name}**.\n\n"
                "The weight of the curse was too great. You have been expelled from the battlefield "
                "to recover your physical form."
            ),
            color=0x000000
        )
        embed.set_footer(text="Death is but a transition in the world of Jujutsu.")
        
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            # Silently fail if player has DMs disabled
            pass
            
        return True
    except Exception as e:
        print(f"Fatality System Error: {e}")
        return False

async def check_binding_vow(user_id, vow_name):
    """
    Checks if a player has a specific Binding Vow active.
    Binding Vows act as passive modifiers in the player document.
    """
    player = await db.players.find_one({"_id": str(user_id)})
    if not player: 
        return False
    
    # Check the 'binding_vows' list within the player data
    vows = player.get("binding_vows", [])
    return vow_name in vows
    
