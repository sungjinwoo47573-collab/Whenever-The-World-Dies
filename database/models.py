def player_model(user_id, username):
    return {
        "_id": str(user_id),
        "name": username,
        "level": 1,
        "xp": 0,
        "money": 500,
        "technique": "None",
        "clan": "None",
        "equipped_weapon": "Fists",
        "stats": {
            "max_hp": 100, "current_hp": 100,
            "max_ce": 50, "cur_ce": 50,
            "dmg": 10, "spd": 5
        },
        "inventory": [],
        "mastery": {}
    }
    
