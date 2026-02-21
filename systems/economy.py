import random
from database.connection import db

async def distribute_rewards(ctx, channel_id, npc_data):
    """
    Handles Loot, Yen, and MVP bonuses after a Curse is exorcised.
    """
    from systems.combat.py import active_combats # Lazy import to avoid circular dependency
    
    combat_data = active_combats.get(channel_id)
    if not combat_data:
        return

    players_dmg = combat_data["players"] # {user_id: total_damage}
    total_npc_hp = npc_data["max_hp"]
    
    # 1. Determine MVP (Highest Damage)
    mvp_id = max(players_dmg, key=players_dmg.get)
    
    results = []

    for user_id, dmg in players_dmg.items():
        # ANTI-LEECH: Must do at least 5% of the boss's HP to get rewards
        if (dmg / total_npc_hp) < 0.05:
            continue
            
        # 2. Calculate Base Yen Reward
        yen_reward = random.randint(100, 500)
        if npc_data.get("is_boss"):
            yen_reward *= 5 # Bosses pay out 5x more
            
        # 3. MVP Bonus (Double Yen + Rare Drop Chance)
        is_mvp = (user_id == mvp_id)
        if is_mvp:
            yen_reward *= 2
            
        # 4. Update Database
        await db.players.update_one(
            {"_id": str(user_id)},
            {"$inc": {"money": yen_reward}}
        )
        
        results.append({
            "user_id": user_id,
            "yen": yen_reward,
            "mvp": is_mvp
        })

    # Clear combat data after rewards are sent
    if channel_id in active_combats:
        del active_combats[channel_id]
        
    return results

async def get_market_stock():
    """
    Logic for the rotating shop. Filters techniques by rarity.
    """
    # Fetches 3 random techniques from the database for the shop
    cursor = db.techniques.aggregate([{"$sample": {"size": 3}}])
    return await cursor.to_list(length=3)
  
