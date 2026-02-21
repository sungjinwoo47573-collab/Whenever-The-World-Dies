import math

def calculate_wb_phase(current_hp, max_hp):
    """
    Phase 1: 100% - 66% HP (1.3x Base DMG)
    Phase 2: 65% - 31% HP (2.6x Base DMG)
    Phase 3: 30% - 0% HP (3.9x Base DMG)
    """
    percentage = (current_hp / max_hp) * 100
    
    if percentage > 65:
        return 1, 1.3
    elif percentage > 30:
        return 2, 2.6
    else:
        return 3, 3.9

def get_aoe_targets(raid_channel):
    """Returns all non-bot members in the raid channel."""
    return [m for m in raid_channel.members if not m.bot]
  
