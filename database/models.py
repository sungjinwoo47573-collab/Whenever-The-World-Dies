import time

def player_model(user_id, username):
    """
    Blueprint for a new Sorcerer.
    Includes stats for HP/CE, Grade roles, and the loadout for !CE commands.
    """
    return {
        "_id": str(user_id),
        "name": username,
        "level": 1,
        "xp": 0,
        "grade": "Grade 4 Sorcerer",
        "money": 0,
        "stat_points": 0,
        "stats": {
            "hp": 100, "max_hp": 100,
            "ce": 50, "max_ce": 50,
            "dmg": 10
        },
        "inventory": [],
        # Loadout maps !CE1-5, !F1-3, and !W1-4 slots
        "loadout": {
            "technique": None, 
            "weapon": None, 
            "style": "Basic Brawling"
        },
        "mastery": {}, # Track skill usage: {"Divergent Fist": 5}
        "vows": [],    # List of active Binding Vows
        "created_at": time.time()
    }

def npc_model(name, is_boss, hp, dmg, img):
    """
    Blueprint for the Fused NPC Creator.
    Combines basic stats with moveset mapping for Boss AI.
    """
    return {
        "name": name,
        "is_boss": is_boss,
        "image": img,
        "hp": hp,
        "max_hp": hp,
        "base_dmg": dmg,
        # Moveset used by systems/combat.py AI loop
        "moveset": {
            "tech": None, 
            "weapon": None, 
            "style": None
        },
        "drops": [], # List of dicts: [{"item_id": "sword_01", "chance": 0.1}]
        "spawn_channels": [], # Channel IDs where this NPC is allowed to appear
        "last_spawn": 0
    }

def technique_model(name, rarity, cost, slots):
    """
    Blueprint for custom Cursed Techniques.
    """
    return {
        "name": name,
        "rarity": rarity, # Common, Rare, Special Grade
        "buy_price": cost,
        "slots": slots,   # Dict mapping of DMG/CE for !CE1 through !CE5
    }
  
