import discord
from config import MAIN_COLOR, THUMBNAIL_URL, BANNER_URL, FOOTER_TEXT, FOOTER_ICON

class PlayerSchema:
    """The complete Sorcerer Profile structure."""
    def __init__(self, user_id: int):
        self.data = {
            "user_id": user_id,
            "level": 1,
            "xp": 0,
            "money": 0,
            "grade": "Grade 4",
            "stat_points": 0,
            # Core Stats
            "hp": 100,
            "max_hp": 100,
            "dmg": 10,
            "stm": 50,
            "max_stm": 50,
            "ce": 50,
            "max_ce": 50,
            # Gear & Mastery
            "weapon": "None",
            "fighting_style": "Basic",
            "cursed_technique": "None",
            "domain": "None",
            "clan": "None",
            # Mastery Levels
            "mastery_ct": 0,
            "mastery_weapon": 0,
            "mastery_style": 0,
            # Buffs from Clans/Items
            "hp_buff": 0,
            "dmg_buff": 0,
            "stm_buff": 0,
            "ce_buff": 0
        }

class NPCSchema:
    """Structure for World Bosses and Raid Bosses."""
    def __init__(self, name, grade, is_raid, drop_item, drop_chance, image_url, weapon_drop):
        self.data = {
            "name": name,
            "grade": grade,
            "is_raid_boss": is_raid,  # True or False
            "drop_item": drop_item,
            "drop_chance": drop_chance,
            "image_url": image_url,
            "weapon_drop": weapon_drop,
            "dialogues": [],
            "hp_multiplier": 1.0  # Used for Raid scaling (+20% per player)
        }

class ClanSchema:
    """Structure for Clan Buffs."""
    def __init__(self, name, hp, dmg, stm, ce):
        self.data = {
            "name": name,
            "hp_buff": hp,
            "dmg_buff": dmg,
            "stm_buff": stm,
            "ce_buff": ce
        }

def get_grade_by_level(level: int) -> str:
    """Logic: 1-Grade 4, 20-Grade 4, 40-Grade 3, 60-Grade 2, 80-Grade 1, 100-Special Grade"""
    if level >= 100: return "Special Grade"
    if level >= 80: return "Grade 1"
    if level >= 60: return "Grade 2"
    if level >= 40: return "Grade 3"
    return "Grade 4"
    
