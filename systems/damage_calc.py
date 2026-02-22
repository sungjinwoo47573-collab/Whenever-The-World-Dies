import random

def calculate_final_damage(player_data, skill_data):
    """
    Customized for our JJK Bot.
    Scales based on player dmg stat and specific skill mastery.
    """
    # 1. Get Base Damage from the skill_buff set earlier
    # Uses 'damage' key from your SkillsCog logic
    base_dmg = skill_data.get("damage", 10) 
    
    # 2. Get Player Attack Stat
    player_stats = player_data.get("stats", {})
    player_atk = player_stats.get("dmg", 5)
    
    # 3. Get Mastery for the specific move title
    # mastery is stored as { "Move Name": points } 
    move_title = skill_data.get("move_title", "Unknown Move")
    mastery_points = player_data.get("mastery", {}).get(move_title, 0)
    
    # Mastery Multiplier: Every 100 points = +100% damage (x2)
    mastery_mult = 1 + (mastery_points / 100)
    
    # 4. Final Calculation
    # Formula: (Base + (Stat * 0.5)) * Mastery Multiplier
    final_dmg = (base_dmg + (player_atk * 0.5)) * mastery_mult
    
    # 5. Critical Hit (Check for 'Black Flash' flavor?)
    is_crit = random.random() < 0.05
    if is_crit:
        final_dmg *= 1.5
        
    return int(final_dmg), is_crit

def can_afford_skill(player_data, skill_data):
    """Checks if the player has enough CE to use the technique."""
    current_ce = player_data.get("stats", {}).get("cur_ce", 0)
    cost = skill_data.get("ce_cost", 0)
    return current_ce >= cost
  
