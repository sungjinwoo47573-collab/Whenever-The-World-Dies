import random

def calculate_final_damage(player_data, skill_data):
    """
    Calculates final damage output for Techniques, Weapons, and Styles.
    Formula: (Base + (Atk Stat * 0.5)) * (1 + (Mastery / 100))
    """
    # 1. Fetch Base Damage set by Admin in /skill_buff
    base_dmg = skill_data.get("damage", 10) 
    
    # 2. Get Player Damage Stat
    player_stats = player_data.get("stats", {})
    player_atk = player_stats.get("dmg", 5)
    
    # 3. Fetch Mastery for the specific move title
    move_title = skill_data.get("move_title", "Basic Attack")
    mastery_points = player_data.get("mastery", {}).get(move_title, 0)
    
    # Mastery Scaling: Every 100 points effectively doubles the damage
    mastery_mult = 1 + (mastery_points / 100)
    
    # 4. Core Calculation
    final_dmg = (base_dmg + (player_atk * 0.5)) * mastery_mult
    
    # 5. Black Flash (Critical Hit) Logic - 7% Base Chance
    is_crit = random.random() < 0.07
    if is_crit:
        final_dmg *= 1.5
        
    return int(final_dmg), is_crit

def can_afford_ce(player_data, cost):
    """Checks if the player has enough Cursed Energy to perform a technique."""
    current_ce = player_data.get("stats", {}).get("cur_ce", 0)
    return current_ce >= cost
    
