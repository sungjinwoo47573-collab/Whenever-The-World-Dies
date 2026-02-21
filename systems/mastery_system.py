from database.connection import db

async def process_mastery_drop(npc_name, player_id):
    """
    Called when an NPC is killed. Pulls the mastery amount 
    assigned to that NPC and applies it to the player's 
    currently equipped Loadout.
    """
    # 1. Get the mastery amount for this NPC
    npc_config = await db.npcs.find_one({"name": npc_name})
    mastery_amt = npc_config.get("mastery_drop", 10)
    
    # 2. Get player's current loadout
    player = await db.players.find_one({"_id": str(player_id)})
    loadout = player.get("loadout", {})

    # 3. Apply mastery to equipped Tech, Weapon, and Style
    update_data = {}
    for category in ["technique", "weapon", "fighting_style"]:
        equipped_name = loadout.get(category)
        if equipped_name:
            # Increments mastery specifically for that item name
            field = f"mastery.{equipped_name}"
            update_data[field] = mastery_amt

    if update_data:
        await db.players.update_one(
            {"_id": str(player_id)},
            {"$inc": update_data}
        )

async def check_skill_unlocked(player_id, skill_name, required_mastery):
    """Checks if a player has enough mastery to use a high-level !CE skill."""
    player = await db.players.find_one({"_id": str(player_id)})
    current_m = player.get("mastery", {}).get(skill_name, 0)
    return current_m >= required_mastery
  
