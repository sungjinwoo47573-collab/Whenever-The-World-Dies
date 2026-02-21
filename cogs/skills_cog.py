import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.checks import is_admin

class SkillsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="skill_buff", description="Set DMG and Effects (Burn, Drain, etc) for a skill.")
    @is_admin()
    async def skill_buff(self, interaction: discord.Interaction, name: str, damage: int, effect: str = None):
        """
        Sets the math and status effects for a specific skill name.
        Example: /skill_buff name: Dismantle damage: 50 effect: Bleed
        """
        skill_data = {
            "name": name,
            "damage": damage,
            "effect": effect.capitalize() if effect else None
        }
        # Save to a global skills library
        await db.db["skills_library"].update_one(
            {"name": name},
            {"$set": skill_data},
            upsert=True
        )
        await interaction.response.send_message(f"✨ Skill **{name}** set to **{damage} DMG** with effect: **{effect or 'None'}**.")

    @app_commands.command(name="boss_moves", description="Assign a Technique, Weapon, and Fighting style to a Boss.")
    @is_admin()
    async def boss_moves(self, interaction: discord.Interaction, npc_name: str, technique: str, weapon: str, fighting: str):
        """
        Forces the Boss AI to pull moves from these specific categories.
        """
        moveset = {
            "tech": technique,
            "weapon": weapon,
            "style": fighting
        }
        result = await db.npcs.update_one(
            {"name": npc_name},
            {"$set": {"moveset": moveset}}
        )
        if result.matched_count > 0:
            await interaction.response.send_message(f"👹 **{npc_name}** moveset updated. They will now use {technique}, {weapon}, and {fighting} skills.")
        else:
            await interaction.response.send_message("❌ NPC not found.")

    @app_commands.command(name="weapon_skill_set", description="Define the skills for a specific weapon.")
    @is_admin()
    async def weapon_skills(self, interaction: discord.Interaction, weapon_name: str, s1: str, s2: str, s3: str):
        """Maps !W1, !W2, !W3 to a weapon."""
        await db.items.update_one(
            {"name": weapon_name, "is_weapon": True},
            {"$set": {"skills": {"1": s1, "2": s2, "3": s3}}}
        )
        await interaction.response.send_message(f"⚔️ Weapon **{weapon_name}** skills set to: {s1}, {s2}, {s3}.")

    @app_commands.command(name="domain_set", description="Configure Domain Expansion for a technique.")
    @is_admin()
    async def domain_set(self, interaction: discord.Interaction, technique_name: str, domain_name: str, hp_buff: int, dmg_buff: int, ce_buff: int):
        """Sets the specific buffs a player gets when they use !Domain."""
        domain_data = {
            "name": domain_name,
            "buffs": {"hp": hp_buff, "dmg": dmg_buff, "ce": ce_buff}
        }
        await db.techniques.update_one(
            {"name": technique_name},
            {"$set": {"domain": domain_data}}
        )
        await interaction.response.send_message(f"🤞 Domain **{domain_name}** linked to **{technique_name}**.")

async def setup(bot):
    await bot.add_cog(SkillsCog(bot))
                         
