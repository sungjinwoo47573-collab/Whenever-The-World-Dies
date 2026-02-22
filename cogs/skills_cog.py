import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
from utils.checks import has_profile

class SkillsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="skills", description="View your manifested Cursed Technique and unlocked skills.")
    @has_profile()
    async def skills(self, interaction: discord.Interaction):
        """Displays the player's technique, unlocked moves, and damage stats."""
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})
        
        # 1. Check if the player has a technique manifested
        ct_name = player.get("technique", "None")
        if ct_name == "None":
            return await interaction.response.send_message(
                "❌ You haven't manifested a Cursed Technique yet. Visit the shop or roll for a lineage!", 
                ephemeral=True
            )

        # 2. Fetch the technique data
        ct_data = await db.techniques.find_one({"name": ct_name})
        if not ct_data:
            return await interaction.response.send_message("⚠️ Your technique data is missing from the archives.", ephemeral=True)

        # 3. Fetch all combat skills belonging to this specific CT
        cursor = db.skills.find({"parent_ct": ct_name})
        all_skills = await cursor.to_list(length=20)

        embed = discord.Embed(
            title=f"🌀 Manifestation: {ct_name}",
            description=f"*{ct_data.get('description', 'No description available.')}*",
            color=0x9b59b6
        )
        
        player_level = player.get("level", 1)
        player_mastery = player.get("mastery", {})
        
        # 4. Loop through skills and determine unlocked status
        if not all_skills:
            embed.add_field(name="Skills", value="No moves registered for this technique yet.", inline=False)
        else:
            for skill in all_skills:
                # Compare player level to the skill's required level
                is_unlocked = player_level >= skill.get("min_level", 1)
                status = "✅" if is_unlocked else f"🔒 (Lv. {skill['min_level']})"
                
                # Get mastery for this specific move title
                move_title = skill.get("move_title", "Unknown")
                mastery_score = player_mastery.get(move_title, 0)
                
                skill_info = (
                    f"**DMG:** `{skill.get('damage', 0)}` | **Cost:** `{skill.get('ce_cost', 0)} CE`\n"
                    f"**Mastery:** `{mastery_score}`"
                )
                
                embed.add_field(
                    name=f"{status} {move_title}",
                    value=skill_info if is_unlocked else "???",
                    inline=True
                )

        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(SkillsCog(bot))
        
