import discord
from discord import app_commands
from database.connection import db

def is_admin():
    """Restricts command to users with Administrator permissions."""
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

def not_in_combat():
    """Prevents inventory/stat changes during active combat."""
    async def predicate(interaction: discord.Interaction) -> bool:
        from systems.combat import active_combats
        if interaction.channel_id in active_combats:
            await interaction.response.send_message("❌ Your soul is locked in combat! You cannot do this now.", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

async def handle_fatality(member: discord.Member, channel: discord.TextChannel):
    """
    The Fatality Rule: Kicks/Hides the channel from a player when HP hits 0.
    """
    try:
        # Hide the channel from the specific player
        await channel.set_permissions(member, view_channel=False, send_messages=False)
        
        # Send a DM or a system message
        embed = discord.Embed(
            title="💀 FATALITY",
            description=f"You have been defeated by the Curse in {channel.name}. You are expelled from the battlefield.",
            color=0x000000
        )
        try:
            await member.send(embed=embed)
        except:
            pass
            
        return True
    except Exception as e:
        print(f"Fatality Error: {e}")
        return False

async def check_binding_vow(user_id, vow_name):
    """Check if player has a specific binding vow active."""
    player = await db.players.find_one({"_id": str(user_id)})
    if not player: return False
    # Logic to check specific conditions like 'Immortal' or 'Unlimited CE'
    return vow_name in player.get("binding_vows", [])
    
