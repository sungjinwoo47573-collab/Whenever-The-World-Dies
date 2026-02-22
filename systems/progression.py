import discord
from database.connection import db

# Role mapping for Grade Promotions
# Levels required for each rank advancement
RANKS = {
    1: "Grade 4",
    20: "Grade 3",
    40: "Grade 2",
    60: "Grade 1",
    80: "Special Grade"
}

async def add_xp(guild, user_id, amount):
    """
    Handles XP gain, Level Ups, Stat Point rewards, and Grade Promotions.
    Synchronized with the FightingCog and Combat systems.
    """
    player = await db.players.find_one({"_id": str(user_id)})
    if not player:
        return None

    current_xp = player.get("xp", 0) + amount
    level = player.get("level", 1)
    
    # Quadratic Scaling: lvl 1 = 100xp, lvl 10 = 10,000xp
    # Formula: (level^2) * 100
    xp_needed = (level ** 2) * 100 

    if current_xp >= xp_needed:
        # Level Up Logic
        new_level = level + 1
        overflow_xp = current_xp - xp_needed
        stat_points_gain = 5
        
        update_data = {
            "xp": overflow_xp,
            "level": new_level,
            "stat_points": player.get("stat_points", 0) + stat_points_gain
        }

        # Handle Grade Promotion if applicable
        promoted_grade = None
        for lvl_req, grade_name in sorted(RANKS.items(), reverse=True):
            if new_level >= lvl_req:
                if player.get("grade") != grade_name:
                    update_data["grade"] = grade_name
                    promoted_grade = grade_name
                    # Sync with Discord Roles
                    await update_discord_role(guild, user_id, grade_name)
                break

        await db.players.update_one({"_id": str(user_id)}, {"$set": update_data})
        
        return {
            "new_level": new_level,
            "grade": promoted_grade,
            "points": stat_points_gain
        }
    
    # Standard XP Update
    await db.players.update_one({"_id": str(user_id)}, {"$set": {"xp": current_xp}})
    return False

async def add_mastery(user_id, item_name, amount):
    """
    Increments mastery for a specific item (Technique, Weapon, or Style).
    Stored in player.mastery as { 'Item Name': total_points }
    """
    if not item_name or item_name == "None":
        return

    # Use a sanitized key to avoid issues with MongoDB
    sanitized_name = str(item_name).replace(".", "_")
    field = f"mastery.{sanitized_name}"
    
    await db.players.update_one(
        {"_id": str(user_id)},
        {"$inc": {field: amount}}
    )

async def update_discord_role(guild, user_id, grade_name):
    """
    Manages Discord roles based on Grade. 
    Removes lower-tier roles to keep the member list clean.
    """
    if not guild:
        return

    member = guild.get_member(int(user_id))
    if not member:
        return

    # Identify all possible "Grade" roles to remove
    grade_keywords = ["Grade 4", "Grade 3", "Grade 2", "Grade 1", "Special Grade"]
    to_remove = [role for role in member.roles if role.name in grade_keywords]
    
    # Get or Create the new role
    new_role = discord.utils.get(guild.roles, name=grade_name)
    if not new_role:
        try:
            # Visual hierarchy: Special Grade is a distinct Red, others are Blue.
            role_color = discord.Color.from_rgb(255, 0, 0) if "Special" in grade_name else discord.Color.blue()
            new_role = await guild.create_role(name=grade_name, color=role_color, hoist=True)
        except discord.Forbidden:
            return

    try:
        # Atomic role update: remove old, add new
        if to_remove:
            await member.remove_roles(*to_remove)
        await member.add_roles(new_role)
    except (discord.Forbidden, discord.HTTPException):
        pass
    
