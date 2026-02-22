import math
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
            # Dynamic key: mastery.Shrine or mastery.Playful_Cloud
            # We sanitize the name to ensure MongoDB keys don't contain illegal characters
            sanitized_name = str(item_name).replace(".", "_")
            field = f"mastery.{sanitized_name}"
            update_query[field] = mastery_amt

    if update_query:
        await db.players.update_one(
            {"_id": str(player_id)},
            {"$inc": update_query}
        )

def calculate_mastery_level(points):
    """
    Converts raw points into a Mastery Tier (1-10).
    Formula: Levels increase exponentially using a square root curve.
    
    Level 1: 0 pts
    Level 2: 100 pts
    Level 3: 400 pts
    Level 4: 900 pts
    ...
    Level 10: 8,100 pts
    """
    if points <= 0: 
        return 1
        
    # Formula: Level = sqrt(points / 100) + 1
    # Example: sqrt(400 / 100) + 1 = 2 + 1 = Level 3
    level = int(math.sqrt(points / 100)) + 1
    return min(level, 10) # Hard cap at Mastery Level 10

async def check_skill_unlocked(player_id, item_name, required_level):
    """
    Checks if the player's Mastery Level for a specific item 
    meets the requirement for advanced moves (e.g., !CE 3).
    """
    player = await db.players.find_one({"_id": str(player_id)})
    if not player:
        return False
        
    sanitized_name = str(item_name).replace(".", "_")
    raw_points = player.get("mastery", {}).get(sanitized_name, 0)
    current_level = calculate_mastery_level(raw_points)
    
    return current_level >= required_level
    
