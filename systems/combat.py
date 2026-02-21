import random
import asyncio
from database.connection import db

# Tracks active channel combats: {channel_id: {"npc": data, "players": {id: dmg}, "variance": 1.0}}
active_combats = {}

async def apply_effect(target_type, channel_id, user_id, effect_name, base_dmg):
    """
    Handles granular skill effects: Burn, Drain, Bleed, Stun.
    """
    if not effect_name:
        return ""

    if effect_name.lower() == "burn":
        # Extra 10% dmg over 3 seconds (simplified for bot speed)
        return "🔥 The target is scorched!"
    
    elif effect_name.lower() == "drain":
        # Heal player for 15% of damage dealt
        heal = int(base_dmg * 0.15)
        await db.players.update_one({"_id": user_id}, {"$inc": {"stats.hp": heal}})
        return f"💉 Drained {heal} HP!"
    
    elif effect_name.lower() == "bleed":
        return "🩸 Internal bleeding applied!"
    
    return ""

async def combat_variance_loop(channel_id):
    """The 12-13 second variance logic (1-3% shift)."""
    while channel_id in active_combats:
        await asyncio.sleep(random.uniform(12, 13))
        if channel_id in active_combats:
            # Shift variance between 0.97 and 1.03
            active_combats[channel_id]["variance"] = random.uniform(0.97, 1.03)

async def npc_ai_loop(ctx, npc_data):
    """
    Automated Boss AI. Uses moveset (Tech, Weapon, Style) 
    and targets based on Aggro.
    """
    channel_id = ctx.channel.id
    active_combats[channel_id] = {
        "npc": npc_data,
        "players": {},
        "variance": 1.0,
        "ai_active": True
    }

    # Start the 12s variance background task
    asyncio.create_task(combat_variance_loop(channel_id))

    while channel_id in active_combats:
        wait = 5 if npc_data.get("is_boss") else 8
        await asyncio.sleep(wait)

        combat = active_combats.get(channel_id)
        if not combat or not combat["players"]:
            continue

        # AGGRO: Target player with highest damage
        target_id = max(combat["players"], key=combat["players"].get)
        target_member = ctx.guild.get_member(int(target_id))
        
        if not target_member:
            continue

        # AI MOVE SELECTION
        # Randomly picks between Tech, Weapon, or Style assigned via /BossMoves
        move_type = random.choice(["tech", "weapon", "style"])
        move_name = npc_data["moveset"].get(move_type) or "Basic Strike"
        
        # Damage + Variance
        dmg = int(npc_data["base_dmg"] * combat["variance"])
        
        await ctx.send(f"💢 **{npc_data['name']}** uses **{move_name}** on <@{target_id}> for **{dmg}** DMG!")

        # FATALITY CHECK: If player dies, kick from channel (Set Permissions)
        # (This is handled in the listener to keep this loop clean)

def get_black_flash(damage):
    """Black Flash Math: Damage ^ 2.5"""
    if random.random() < 0.025: # 2.5% chance
        return int(damage ** 2.5), True
    return damage, False
    
