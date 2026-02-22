from database.connection import db

async def get_tech_stats(user_id):
    """Calculates player stats including Technique buffs and Mastery scaling."""
    player = await db.players.find_one({"_id": str(user_id)})
    if not player or player.get("technique") == "None":
        return None

    tech_name = player["technique"]
    tech_data = await db.techniques.find_one({"name": tech_name})
    
    if not tech_data:
        return None

    # Mastery Scaling: 1% extra power per 100 Mastery points
    mastery = player.get("mastery", {}).get(tech_name, 0)
    mastery_multiplier = 1 + (mastery / 10000) 

    final_ce_buff = tech_data.get("ce_buff", 1.0) * mastery_multiplier
    final_dmg_buff = tech_data.get("dmg_buff", 1.0) * mastery_multiplier

    return {
        "name": tech_name,
        "ce_multi": round(final_ce_buff, 2),
        "dmg_multi": round(final_dmg_buff, 2),
        "mastery": mastery
    }
  
