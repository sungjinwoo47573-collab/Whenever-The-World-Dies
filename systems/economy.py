import random
from database.connection import db

async def distribute_rewards(ctx, channel_id, npc_data):
    """
    Handles Money Drops, Item Looting, and XP distribution.
    Includes the Highest Damage Bonus and Equal Split logic.
    """
    from systems.combat import active_combats
    
    combat_data = active_combats.get(channel_id)
    if not combat_data:
        return

    players_dmg = combat_data["players"]
    if not players_dmg:
        return

    # 1. Identify MVP (Highest Damage)
    mvp_id = max(players_dmg, key=players_dmg.get)
    
    # 2. Get Money Drop configuration
    base_money = npc_data.get("money_drop", 100)
    base_xp = 200 if npc_data.get("is_boss") else 50

    # 3. Calculate Drops
    # npc_data['drops'] = [{"item": "Sword", "chance": 0.05}]
    possible_drops = npc_data.get("drops", [])

    summary = []
    
    for user_id, dmg in players_dmg.items():
        # Equal Split logic for Money/XP
        money_gain = base_money
        xp_gain = base_xp
        
        # MVP Bonus: Extra 50% Money/XP + Higher Loot Roll
        is_mvp = (user_id == mvp_id)
        loot_multiplier = 1.5 if is_mvp else 1.0
        if is_mvp:
            money_gain = int(money_gain * 1.5)
            xp_gain = int(xp_gain * 1.5)

        # Process Item Loot
        got_items = []
        for drop in possible_drops:
            roll = random.random()
            if roll < (drop["chance"] * loot_multiplier):
                got_items.append(drop["item"])

        # Update Database
        await db.players.update_one(
            {"_id": str(user_id)},
            {
                "$inc": {"money": money_gain, "xp": xp_gain},
                "$push": {"inventory": {"$each": got_items}}
            }
        )

        summary.append({
            "user_id": user_id,
            "money": money_gain,
            "xp": xp_gain,
            "items": got_items,
            "mvp": is_mvp
        })

    return summary

async def get_technique_stock():
    """
    Filters techniques based on their StockChance for the shop.
    """
    all_techs = await db.techniques.find().to_list(length=100)
    stock = []
    for tech in all_techs:
        if random.random() < tech.get("stock_chance", 0.5):
            stock.append(tech)
    return stock
    
