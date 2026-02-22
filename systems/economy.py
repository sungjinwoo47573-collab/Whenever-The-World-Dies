import random
from database.connection import db

async def distribute_rewards(message, channel_id, npc_data):
    """
    Finalizes the exorcism by granting Yen, XP, and Loot.
    Features: MVP Bonus (1.5x), Equal Base Pay, and Rarity-based Looting.
    """
    from systems.combat import active_combats
    
    combat_data = active_combats.get(channel_id)
    if not combat_data or not combat_data.get("players"):
        return None

    players_dmg = combat_data["players"]
    # 1. MVP Identification (Highest Aggro/Damage)
    mvp_id = max(players_dmg, key=players_dmg.get)
    
    # 2. Base Configuration from NPC Data
    base_money = npc_data.get("money_drop", 500)
    base_xp = npc_data.get("xp_drop", 100)
    possible_drops = npc_data.get("drops", []) # Format: [{"item": "Dragon Bone", "chance": 0.05}]

    reward_summary = []
    
    for user_id, dmg in players_dmg.items():
        # 3. Calculate Scaling
        is_mvp = (user_id == mvp_id)
        # MVP receives a 50% boost to currency and XP
        money_gain = int(base_money * (1.5 if is_mvp else 1.0))
        xp_gain = int(base_xp * (1.5 if is_mvp else 1.0))
        
        # 4. Process Loot (MVP gets a 20% luck bonus on drop rates)
        loot_luck = 1.2 if is_mvp else 1.0
        earned_items = []
        for drop in possible_drops:
            roll = random.random()
            if roll < (drop.get("chance", 0.01) * loot_luck):
                earned_items.append(drop["item"])

        # 5. Database Update: Bulk increment stats and push items to inventory
        await db.players.update_one(
            {"_id": str(user_id)},
            {
                "$inc": {"money": money_gain, "xp": xp_gain},
                "$push": {"inventory": {"$each": earned_items}}
            }
        )

        reward_summary.append({
            "user_id": user_id,
            "money": money_gain,
            "xp": xp_gain,
            "items": earned_items,
            "is_mvp": is_mvp
        })

    # Note: FightingCog's add_xp logic should be called after this 
    # to handle level-ups for all participants.
    return reward_summary

async def get_technique_stock():
    """
    The 'Black Market' Logic: Rotates available techniques based on stock chance.
    Typically called by the Shop system or a background task.
    """
    cursor = db.techniques.find({"stock_chance": {"$gt": 0}})
    all_techs = await cursor.to_list(length=100)
    
    currently_available = []
    for tech in all_techs:
        # If stock_chance is 0.1, it has a 10% chance to appear today
        if random.random() < tech.get("stock_chance", 0.5):
            currently_available.append(tech)
            
    return currently_available
        
