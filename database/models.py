import time

def player_model(user_id, username):
    """
    Initializes a new sorcerer. 
    Synchronized with CombatCog and WorldBossCog requirements.
    """
    return {
        "_id": str(user_id),
        "name": username,
        "level": 1,
        "xp": 0,
        "money": 500, # Starting Yen
        "stat_points": 5,
        "grade": "Grade 4",
        "clan": "None",
        "clan_rerolls": 3,
        "stats": {
            "max_hp": 500, 
            "current_hp": 500, 
            "max_ce": 100, 
            "current_ce": 100, 
            "dmg": 20
        },
        "inventory": [], # List of strings: ["Shrine", "Playful Cloud"]
        "loadout": {
            "technique": None, 
            "weapon": None, 
            "fighting_style": None
        },
        "mastery": {}, # Track proficiency: {"Shrine": 120}
        "created_at": time.time()
    }

def clan_model(name, hp_buff, ce_buff, dmg_buff, roll_chance):
    """
    Standardized for the ClanCog reroll logic.
    """
    return {
        "name": name,
        "hp_buff": hp_buff,
        "ce_buff": ce_buff,
        "dmg_buff": dmg_buff,
        "roll_chance": roll_chance # 0.01 = 1%
    }

def technique_model(name, stock_chance, price=0):
    """
    Blueprint for Cursed Techniques in the Gacha/Shop.
    """
    return {
        "name": name,
        "stock_chance": stock_chance,
        "price": price,
        "domain": None # Configured via /domain_set
    }

def npc_model(name, hp, dmg, img, is_world_boss=False):
    """
    The blueprint for both regular Curses and World Bosses.
    """
    return {
        "name": name,
        "is_world_boss": is_world_boss,
        "max_hp": hp,
        "current_hp": hp,
        "base_dmg": dmg,
        "image": img,
        "phase": 1,
        "technique": None, # For reactive boss moves
        "weapon": None,
        "fighting_style": None,
        "mastery_drop": 50,
        "money_drop": 1000,
        "drops": [] # List of dicts: {"item": str, "chance": float}
    }

def skill_model(name, move_number, move_title, damage, rarity="Common"):
    """
    The move blueprint for !CE, !W, and !F combat commands.
    """
    return {
        "name": name,           # Linked Technique/Weapon name
        "move_number": move_number, # 1, 2, or 3
        "move_title": move_title,   # e.g., "Divergent Fist"
        "damage": damage,
        "rarity": rarity,
        "effect": None
    }

def item_model(name, price, is_weapon=True, dmg_buff=0, hp_buff=0):
    """
    Used for Weapons and Accessories.
    """
    return {
        "name": name,
        "price": price,
        "is_weapon": is_weapon,
        "dmg_buff": dmg_buff,
        "hp_buff": hp_buff
    }
    
