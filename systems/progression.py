import discord
from database.connection import db

# Role mapping for Auto-Ranking
RANKS = {
    1: "Grade 4 Sorcerer",
    15: "Grade 3 Sorcerer",
    30: "Grade 2 Sorcerer",
    50: "Grade 1 Sorcerer",
    80: "Special Grade Sorcerer"
}

async def add_xp(guild, user_id, amount):
    """Adds XP and handles Level Up + Auto-Ranking."""
    player = await db.players.find_one({"_id": str(user_id)})
    if not player:
        return

    new_xp = player.get("xp", 0) + amount
    lvl = player.get("level", 1)
    xp_needed = lvl * 150 # Scaling XP requirement

    if new_xp >= xp_needed:
        # Level Up!
        lvl += 1
        new_xp = 0
        stat_points = 5
        
        update_fields = {
            "xp": new_xp,
            "level": lvl,
            "stat_points": player.get("stat_points", 0) + stat_points
        }

        # Check for Grade Promotion
        if lvl in RANKS:
            new_grade = RANKS[lvl]
            update_fields["grade"] = new_grade
            await update_discord_role(guild, user_id, new_grade)

        await db.players.update_one({"_id": str(user_id)}, {"$set": update_fields})
        return True # Signifies a level up occurred
    
    await db.players.update_one({"_id": str(user_id)}, {"$set": {"xp": new_xp}})
    return False

async def add_mastery(user_id, skill_name, amount):
    """Increases mastery for a specific skill, technique, or weapon."""
    # Mastery is stored as: mastery: {"Divergent Fist": 120}
    field = f"mastery.{skill_name}"
    await db.players.update_one(
        {"_id": str(user_id)},
        {"$inc": {field: amount}}
    )

async def update_discord_role(guild, user_id, grade_name):
    """Removes old Grade roles and adds the new one."""
    member = guild.get_member(int(user_id))
    if not member: return

    # Clean up old roles containing "Sorcerer"
    to_remove = [r for r in member.roles if "Sorcerer" in r.name]
    role = discord.utils.get(guild.roles, name=grade_name)
    
    if not role:
        role = await guild.create_role(name=grade_name, color=discord.Color.gold())

    try:
        await member.remove_roles(*to_remove)
        await member.add_roles(role)
    except discord.Forbidden:
        pass
        
