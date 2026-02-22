from database.connection import db

async def process_mastery_drop(npc_name, player_id):
    """
    Distributes Mastery points upon an NPC's exorcism.
    Points are applied only to the items currently in the player's LOADOUT.
    """
    # 1. Fetch the mastery reward defined for this NPC
    npc_config = await db.npcs.find_one({"name": npc_name})
    if not npc_config:
        return
        
    mastery_amt = npc_config.get("mastery_drop", 10)
    
    # 2. Identify what the player was using during the fight
    player = await db.players.find_one({"_id": str(player_id)})
    if not player:
        return
        
    loadout = player.get("loadout", {})
    update_query = {}

    # 3. Apply points to Technique, Weapon, and Fighting Style
    # This allows a player to master multiple tools simultaneously.
    for category in ["technique", "weapon", "fighting_style"]:
        item_name = loadout.get(category)
        if item_name and item_name != "None":
            # Example path: mastery.Dismantle_and_Cleave
            field = f"mastery.{item_name}"
            update_query[field] = mastery_amt

    if update_query:
        await db.players.update_one(
            {"_id": str(player_id)},
            {"$inc": update_query}
        )

def calculate_mastery_level(points):
    """
    Converts raw points into a Mastery Tier (1-10).
    Formula: Levels increase exponentially (Level 2 = 100pts, Level 3 = 400pts, etc.)
    """
    if points <= 0: return 1
    # Simple curve: Level = sqrt(points / 100) + 1
    import math
    level = int(math.sqrt(points / 100)) + 1
    return min(level, 10) # Cap at Mastery Level 10

async def check_skill_unlocked(player_id, item_name, required_level):
    """
    Checks if the player's Mastery Level for a specific item 
    meets the requirement for a specific move (e.g., !CE 3).
    """
    player = await db.players.find_one({"_id": str(player_id)})
    if not player:
        return False
        
    raw_points = player.get("mastery", {}).get(item_name, 0)
    current_level = calculate_mastery_level(raw_points)
    
    return current_level >= required_level
    
