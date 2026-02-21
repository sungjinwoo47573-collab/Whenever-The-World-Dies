import random
import asyncio
from database.connection import db

# Global tracker for active fights: {channel_id: {"players": {user_id: damage}, "variance": 1.0}}
active_combats = {}

async def calculate_variance(channel_id):
    """
    The 'Entropy' logic. Every 12-13 seconds, the Boss's power shifts.
    This runs as a background task during a fight.
    """
    while channel_id in active_combats:
        # Wait for the specific 12-13 second window
        await asyncio.sleep(random.uniform(12, 13))
        
        if channel_id in active_combats:
            # Shift variance between 0.97 (-3%) and 1.03 (+3%)
            new_variance = random.uniform(0.97, 1.03)
            active_combats[channel_id]["variance"] = new_variance

async def npc_auto_attack_loop(ctx, npc_data):
    """
    The AI Brain. NPCs wait for an attack, then begin a retaliatory loop.
    Normal Curses attack every 8s. Bosses attack every 5s.
    """
    channel_id = ctx.channel.id
    
    # Initialize the combat tracking
    active_combats[channel_id] = {
        "npc": npc_data,
        "players": {}, # Tracks damage dealt by each player for Aggro
        "variance": 1.0
    }

    # Start the Variance/Entropy task if it's a Boss
    if npc_data.get("is_boss"):
        asyncio.create_task(calculate_variance(channel_id))

    while channel_id in active_combats:
        # Bosses are faster (5s) than normal mobs (8s)
        wait_time = 5 if npc_data.get("is_boss") else 8
        await asyncio.sleep(wait_time)

        combat_data = active_combats.get(channel_id)
        if not combat_data or not combat_data["players"]:
            continue

        # AGGRO LOGIC: Target the player with the highest Damage Threat
        target_id = max(combat_data["players"], key=combat_data["players"].get)
        target_member = ctx.guild.get_member(int(target_id))

        if not target_member:
            continue

        # DAMAGE CALCULATION with Variance
        base_dmg = npc_data["base_dmg"]
        final_dmg = int(base_dmg * combat_data["variance"])

        # In a full implementation, we would subtract from Player HP here.
        # For now, we announce the attack.
        await ctx.send(f"💢 **{npc_data['name']}** focuses on <@{target_id}> and strikes for **{final_dmg}** DMG!")

async def check_black_flash():
    """
    The 2.5% chance to land a Black Flash.
    Returns True if the sparks turn black.
    """
    return random.random() < 0.025

def apply_black_flash(damage):
    """The math for Black Flash: Damage raised to the power of 2.5."""
    return int(damage ** 2.5)
  
