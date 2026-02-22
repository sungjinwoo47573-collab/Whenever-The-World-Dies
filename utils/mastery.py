import discord
from database.connection import techniques_col, players_col

class MasterySystem:
    @staticmethod
    async def get_mastery_level(player_data, tech_type):
        """
        Retrieves the specific mastery level for CT, Weapon, or Fighting Style.
        """
        mapping = {
            "CT": "mastery_ct",
            "Weapon": "mastery_weapon",
            "FightingStyle": "mastery_style"
        }
        key = mapping.get(tech_type)
        return player_data.get(key, 0) if key else 0

    @staticmethod
    async def check_requirement(user_id, tech_type, skill_slot):
        """
        Checks if a player meets the mastery requirement for a specific skill.
        """
        player = await players_col.find_one({"user_id": user_id})
        if not player:
            return False, "Not registered."

        # Fetch the requirement from the technique/weapon data
        tech_name = player.get(tech_type.lower()) # e.g., player['weapon']
        tech_data = await techniques_col.find_one({"name": tech_name})
        
        if not tech_data:
            return True, "No requirements found." # Default to allowed

        req_key = f"req_skill_{skill_slot}"
        required_mastery = tech_data.get(req_key, 0)
        current_mastery = await MasterySystem.get_mastery_level(player, tech_type)

        if current_mastery >= required_mastery:
            return True, "Success"
        else:
            return False, f"Requires Mastery Level {required_mastery} (Current: {current_mastery})"

    @staticmethod
    async def add_mastery_exp(user_id, tech_type, amount):
        """
        Updates the mastery experience after a successful Boss/Raid exorcism.
        """
        mapping = {
            "CT": "mastery_ct",
            "Weapon": "mastery_weapon",
            "FightingStyle": "mastery_style"
        }
        key = mapping.get(tech_type)
        if key:
            await players_col.update_one(
                {"user_id": user_id},
                {"$inc": {key: amount}}
            )
                
