import discord
from discord import app_commands
from systems.combat import active_combats

def is_admin():
    """
    Check if the user has Administrator permissions.
    Used for /npc_create and other world-building tools.
    """
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

def not_in_combat():
    """
    Prevents players from using specific commands (like /equip or /shop)
    if their channel is currently in an active combat state.
    """
    def predicate(interaction: discord.Interaction) -> bool:
        channel_id = interaction.channel_id
        # If the channel is in the active_combats dict, block the command
        if channel_id in active_combats:
            return False
        return True
    return app_commands.check(predicate)

async def check_fatality(member: discord.Member, current_hp: int):
    """
    The Fatality Rule: If HP hits 0, remove player from the combat channel.
    """
    if current_hp <= 0:
        try:
            # Overwrite permissions to hide the channel from the 'dead' player
            await member.guild.active_channels[0].set_permissions(member, view_channel=False)
            return True
        except:
            return False
    return False
  
