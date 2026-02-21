import time

def player_model(user_id, username):
    return {
        "_id": str(user_id),
        "name": username,
        "level": 1,
        "xp": 0,
        "money": 0,
        "stat_points": 0,
        "stats": {"hp": 100, "max_hp": 100, "ce": 50, "max_ce": 50, "dmg": 10},
        "clan": None,
        "clan_rerolls": 3,
        "inventory": [], # List of item names/IDs
        "techniques": [], # List of purchased techniques
        "loadout": {
            "technique": None, 
            "weapon": None, 
            "fighting_style": None,
            "accessory": None
        },
        "mastery": {}, # e.g., {"Divergent Fist": 50}
        "grade": "Grade 4 Sorcerer",
        "created_at": time.time()
    }

def clan_model(name, hp_b, ce_b, dmg_b, chance):
    return {
        "name": name,
        "buffs": {"hp": hp_b, "ce": ce_b, "dmg": dmg_b},
        "roll_chance": chance # e.g., 0.01 for 1%
    }

def technique_model(name, stock_chance, price=0):
    return {
        "name": name,
        "stock_chance": stock_chance,
        "price": price,
        "skills": {
            "1": None, "2": None, "3": None, "4": None, "5": None
        },
        "domain": None # Stores domain_model data
    }

def skill_model(name, dmg, effect=None):
    return {
        "name": name,
        "dmg": dmg,
        "effect": effect # "Burn", "Drain", "Bleed", "Stun"
    }

def item_model(name, is_weapon, dmg=0, grade="Grade 4", buffs=None):
    return {
        "name": name,
        "is_weapon": is_weapon,
        "dmg": dmg,
        "grade": grade,
        "buffs": buffs or {"hp": 0, "ce": 0, "dmg": 0} # For accessories
    }

def npc_model(name, is_boss, hp, dmg, img, drops=None):
    return {
        "name": name,
        "is_boss": is_boss,
        "hp": hp,
        "max_hp": hp,
        "base_dmg": dmg,
        "image": img,
        "drops": drops or [], # [{"item": "Name", "chance": 0.1}]
        "money_drop": 0,
        "spawn_channels": [],
        "moveset": {"tech": None, "weapon": None, "style": None}
    }

def raid_model(name, boss_name, drop_name, drop_chance):
    return {
        "name": name,
        "boss": boss_name,
        "drop": drop_name,
        "chance": drop_chance,
        "active": False,
        "players": []
    }
    
