import discord
from database.connection import db

# Configuration for Auto-Ranking Roles
# Level: Role Name
RANKS = {
    1: "Grade 4 Sorcerer",
    15: "Grade 3 Sorcerer",
    30: "Grade 2 Sorcerer",
    50: "Grade 1 Sorcerer",
    80: "Special Grade Sorcerer"
}

async def add_xp(guild, user_id, amount):
    """
    Core function for XP gain. Handles Level Ups and Auto-Ranking.
    Called by player_cog.py whenever a player chats or wins a fight.
    """
    player = await db.players.find_one({"_id": str(user_id)})
    if not player:
        return None

    current_xp = player.get("xp", 0) + amount
    current_level = player.get("level", 1)
    
    # Formula: Each level requires 100 XP (Level 1=100, Level 2=200, etc.)
    xp_needed = current_level * 100

    if current_xp >= xp_needed:
        # LEVEL UP LOGIC
        new_level = current_level + 1
        stat_points_gain = 5
        
        update_data = {
            "xp": 0,
            "level": new_level,
            "stat_points": player.get("stat_points", 0) + stat_points_gain
        }

        # AUTO-RANKING LOGIC
        if new_level in RANKS:
            new_grade = RANKS[new_level]
            update_data["grade"] = new_grade
            # Trigger Discord Role Update
            await update_sorcerer_role(guild, user_id, new_grade)

        await db.players.update_one({"_id": str(user_id)}, {"$set": update_data})
        return {"leveled_up": True, "level": new_level}
    
    # Just update XP
    await db.players.update_one({"_id": str(user_id)}, {"$set": {"xp": current_xp}})
    return {"leveled_up": False}

async def update_sorcerer_role(guild, user_id, grade_name):
    """
    Automatically manages Discord roles. 
    Removes old Grade roles and adds the new one.
    """
    member = guild.get_member(int(user_id))
    if not member:
        return

    # Find or Create the role in the server
    role = discord.utils.get(guild.roles, name=grade_name)
    if not role:
        # Create role if it doesn't exist (Admin doesn't have to pre-make them)
        role = await guild.create_role(name=grade_name, color=discord.Color.dark_gold())

    # Filter out any roles that have "Sorcerer" in the name to clean up old ranks
    old_ranks = [r for r in member.roles if "Sorcerer" in r.name]
    
    try:
        await member.remove_roles(*old_ranks)
        await member.add_roles(role)
    except discord.Forbidden:
        print(f"❌ Error: Bot does not have permission to manage roles for {member.name}")
      
