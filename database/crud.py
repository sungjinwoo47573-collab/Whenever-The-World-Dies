from .connection import players_col
from .models import PlayerSchema, get_grade_by_level

async def get_player(user_id: int):
    """Fetch a player's data from the database."""
    return await players_col.find_one({"user_id": user_id})

async def register_player(user_id: int):
    """Create a new player entry if they don't exist."""
    existing = await get_player(user_id)
    if existing:
        return False
    
    new_sorcerer = PlayerSchema(user_id).data
    await players_col.insert_one(new_sorcerer)
    return True

async def add_money(user_id: int, amount: int):
    """Add or subtract money from a player."""
    await players_col.update_one(
        {"user_id": user_id},
        {"$inc": {"money": amount}}
    )

async def update_xp(user_id: int, xp_amount: int):
    """Add XP and handle level-ups with +3 stat points reward."""
    player = await get_player(user_id)
    if not player:
        return None

    current_xp = player['xp'] + xp_amount
    current_level = player['level']
    # Leveling formula: Level * 250 XP required for next level
    xp_required = current_level * 250

    if current_xp >= xp_required:
        new_level = current_level + 1
        new_grade = get_grade_by_level(new_level)
        
        await players_col.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "xp": 0,
                    "level": new_level,
                    "grade": new_grade
                },
                "$inc": {
                    "stat_points": 3 # 3 Stat points per level
                }
            }
        )
        return {"leveled_up": True, "level": new_level, "grade": new_grade}
    
    await players_col.update_one(
        {"user_id": user_id},
        {"$set": {"xp": current_xp}}
    )
    return {"leveled_up": False}

async def wipe_database_confirmed():
    """Nuclear option: Wipe all player data."""
    await players_col.delete_many({})
    return True
  
