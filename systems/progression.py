from database.connection import db

async def add_xp(guild, user_id, amount):
    """
    Awards XP to a player and checks for level-up.
    Increases HP and CE maximums upon reaching a new level.
    """
    user_id = str(user_id)
    player = await db.players.find_one({"_id": user_id})
    
    if not player:
        return

    current_xp = player.get("xp", 0) + amount
    current_lvl = player.get("level", 1)
    
    # Requirement: Level * 100 XP to reach the next level
    xp_needed = current_lvl * 100
    
    if current_xp >= xp_needed:
        # Level Up Logic
        new_lvl = current_lvl + 1
        new_xp = current_xp - xp_needed
        
        # Stat increases per level
        updates = {
            "level": new_lvl,
            "xp": new_xp,
            "stats.max_hp": player["stats"]["max_hp"] + 20,
            "stats.max_ce": player["stats"]["max_ce"] + 15,
            "stats.current_hp": player["stats"]["max_hp"] + 20,
            "stats.cur_ce": player["stats"]["max_ce"] + 15
        }
        
        await db.players.update_one({"_id": user_id}, {"$set": updates})
        
        # Attempt to notify in a system channel or log if needed
        return True
    else:
        # Just update XP
        await db.players.update_one({"_id": user_id}, {"$set": {"xp": current_xp}})
        return False

async def get_rank(level):
    """Returns the Jujutsu Sorcerer grade based on level."""
    if level < 5: return "Grade 4"
    if level < 15: return "Grade 3"
    if level < 30: return "Grade 2"
    if level < 50: return "Grade 1"
    return "Special Grade"
    
