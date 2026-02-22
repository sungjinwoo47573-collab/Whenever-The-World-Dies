import random
import asyncio
from database.connection import db

# Tracks active channel combats: {channel_id: {"npc": data, "players": {id: dmg}, "variance": 1.0}}
active_combats = {}

async def apply_effect(target_type, channel_id, user_id, effect_name, base_dmg):
    """
    Handles granular skill effects. 
    Synchronized with the rebuilt Player and NPC models.
    """
    if not effect_name:
        return ""

    effect_name = effect_name.lower()

    if effect_name == "burn":
        # Visual indicator for a damage-over-time effect
        return "🔥 The target's cursed energy is combusting!"
    
    elif effect_name == "drain":
        # Heal player for 15% of damage dealt, capped by Max HP
        player = await db.players.find_one({"_id": user_id})
        if player:
            heal_amount = int(base_dmg * 0.15)
            new_hp = min(player['stats']['max_hp'], player['stats']['current_hp'] + heal_amount)
            await db.players.update_one({"_id": user_id}, {"$set": {"stats.current_hp": new_hp}})
            return f"💉 **Drain:** Absorbed `{heal_amount}` HP!"
    
    elif effect_name == "bleed":
        return "🩸 **Hemorrhage:** The target is losing stability!"
    
    return ""

async def combat_variance_loop(channel_id):
    """
    The 'Breathing' System: Shits damage variance every 12-13 seconds.
    This creates the 'highs and lows' of a real battle.
    """
    while channel_id in active_combats:
        await asyncio.sleep(random.uniform(12, 13))
        if channel_id in active_combats:
            # Shift variance between 0.95 and 1.05 (5% fluctuation)
            active_combats[channel_id]["variance"] = random.uniform(0.95, 1.05)

def get_black_flash(damage):
    """
    The spark of black does not choose who to bless.
    Calculates a 2.5% chance for a massive critical hit.
    """
    if random.random() < 0.025: # 2.5% Chance
        # Using a 2.5x multiplier for consistent RPG balancing
        return int(damage * 2.5), True
    return damage, False

async def npc_ai_loop(ctx, npc_data):
    """
    Automated Boss AI. 
    Logic: Targets the player with the highest Aggro (most damage dealt).
    """
    channel_id = ctx.channel.id
    active_combats[channel_id] = {
        "npc": npc_data,
        "players": {}, # Stores {user_id: total_damage_dealt}
        "variance": 1.0,
        "ai_active": True
    }

    # Start the background task for damage variance
    asyncio.create_task(combat_variance_loop(channel_id))

    while channel_id in active_combats:
        # Bosses act every 5 seconds, regular NPCs every 8
        wait_time = 5 if npc_data.get("is_world_boss") else 8
        await asyncio.sleep(wait_time)

        combat = active_combats.get(channel_id)
        if not combat or not combat["players"]:
            continue

        # AGGRO SYSTEM: Find the player who has dealt the most damage
        target_id = max(combat["players"], key=combat["players"].get)
        
        # Select Move
        move_type = random.choice(["technique", "weapon", "fighting_style"])
        move_name = npc_data.get(move_type) or "Basic Cursed Strike"
        
        # Apply Variance to Boss Damage
        variance = combat.get("variance", 1.0)
        final_dmg = int(npc_data.get("base_dmg", 50) * variance)
        
        # Update Player HP in Database
        await db.players.update_one(
            {"_id": str(target_id)},
            {"$inc": {"stats.current_hp": -final_dmg}}
        )

        await ctx.send(
            f"💢 **{npc_data['name']}** focuses their malice on <@{target_id}>!\n"
            f"They use **{move_name}** for **{final_dmg}** damage!"
        )

        # Check if NPC is dead (handled in main listener, but loop cleanup is here)
        current_npc = await db.npcs.find_one({"_id": npc_data["_id"]})
        if not current_npc or current_npc.get("current_hp", 0) <= 0:
            active_combats.pop(channel_id, None)
            break
        
