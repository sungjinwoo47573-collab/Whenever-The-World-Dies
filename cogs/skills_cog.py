import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
from utils.checks import is_admin

class SkillsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="skill_buff", description="Admin: Set DMG, Effects, and Rarity for a specific move.")
    @app_commands.choices(rarity=[
        app_commands.Choice(name="Common", value="Common"),
        app_commands.Choice(name="Rare", value="Rare"),
        app_commands.Choice(name="Epic", value="Epic"),
        app_commands.Choice(name="Legendary", value="Legendary"),
        app_commands.Choice(name="Special Grade", value="Special Grade")
    ])
    @is_admin()
    async def skill_buff(self, interaction: discord.Interaction, name: str, damage: int, rarity: str, effect: str = None):
        """
        Updates the global skills library and the active combat skills.
        """
        skill_data = {
            "move_title": name,
            "damage": damage,
            "rarity": rarity,
            "effect": effect.capitalize() if effect else None
        }
        
        # 1. Update the library for reference
        await db.db["skills_library"].update_one(
            {"move_title": name},
            {"$set": skill_data},
            upsert=True
        )
        
        # 2. Update any active moves in the combat 'skills' collection using this title
        # This ensures currently equipped items reflect the new damage/rarity
        await db.skills.update_many(
            {"move_title": name},
            {"$set": {"damage": damage, "rarity": rarity}}
        )

        embed = discord.Embed(
            title="✨ SKILL TUNING COMPLETE",
            description=f"Move **{name}** has been calibrated.",
            color=0x00fbff
        )
        embed.add_field(name="Stats", value=f"DMG: `{damage}`\nGrade: `{rarity}`\nEffect: `{effect or 'None'}`")
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="weapon_skill_set", description="Admin: Map specific moves to !W1, !W2, and !W3 slots.")
    @is_admin()
    async def weapon_skills(self, interaction: discord.Interaction, weapon_name: str, 
                             s1_name: str, s1_dmg: int, 
                             s2_name: str, s2_dmg: int, 
                             s3_name: str, s3_dmg: int):
        """Maps weapon moves directly to the combat engine's skill collection."""
        
        # Define the three moves for the weapon
        moves = [
            {"move_number": 1, "name": weapon_name, "move_title": s1_name, "damage": s1_dmg},
            {"move_number": 2, "name": weapon_name, "move_title": s2_name, "damage": s2_dmg},
            {"move_number": 3, "name": weapon_name, "move_title": s3_name, "damage": s3_dmg}
        ]
        
        for move in moves:
            await db.skills.update_one(
                {"name": move["name"], "move_number": move["move_number"]},
                {"$set": move},
                upsert=True
            )

        embed = discord.Embed(
            title="⚔️ WEAPON ARSENAL UPDATED",
            description=f"The cursed tool **{weapon_name}** moves are now live.",
            color=0x95a5a6
        )
        embed.add_field(name="Moveset", value=f"1. {s1_name}\n2. {s2_name}\n3. {s3_name}")
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="boss_moves", description="Admin: Assign Technique, Weapon, and Style to a Boss.")
    @is_admin()
    async def boss_moves(self, interaction: discord.Interaction, npc_name: str, technique: str, weapon: str, style: str):
        """Forces the Boss to use specific names for its reactive counter-attacks."""
        updates = {
            "technique": technique,
            "weapon": weapon,
            "fighting_style": style
        }
        
        result = await db.npcs.update_one(
            {"name": npc_name},
            {"$set": updates}
        )

        if result.matched_count > 0:
            embed = discord.Embed(title="👹 BOSS MOVESET SEALED", description=f"**{npc_name}** will now retaliate using these styles.", color=0x2b2d31)
            embed.add_field(name="Loadout", value=f"🌀 CT: {technique}\n⚔️ Weapon: {weapon}\n👊 Style: {style}")
            BannerManager.apply(embed, type="admin")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Boss not found in database.", ephemeral=True)

    @app_commands.command(name="domain_set", description="Admin: Configure Domain Expansion buffs.")
    @is_admin()
    async def domain_set(self, interaction: discord.Interaction, technique_name: str, domain_name: str, hp_buff: int, dmg_buff: int):
        """Sets the buffs for the ultimate technique expansion."""
        domain_data = {
            "name": domain_name,
            "buffs": {"hp": hp_buff, "dmg": dmg_buff}
        }
        await db.techniques.update_one(
            {"name": technique_name},
            {"$set": {"domain": domain_data}}
        )
        
        embed = discord.Embed(
            title="🤞 DOMAIN EXPANSION REGISTERED",
            description=f"**{domain_name}** linked to **{technique_name}**.",
            color=0x000000
        )
        embed.add_field(name="Buffs", value=f"HP: +{hp_buff} | DMG: +{dmg_buff}")
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(SkillsCog(bot))
    
