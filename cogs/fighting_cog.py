import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.checks import is_admin
from utils.banner_manager import BannerManager
import random

class FightingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_grade_from_level(self, level):
        """Maps levels to Jujutsu Sorcerer Grades."""
        if level >= 80: return "Special Grade Sorcerer"
        if level >= 60: return "Grade 1 Sorcerer"
        if level >= 40: return "Grade 2 Sorcerer"
        if level >= 20: return "Grade 3 Sorcerer"
        return "Grade 4 Sorcerer"

    async def add_xp(self, user_id, xp_amount, channel):
        """Handles XP gain, automatic Level-Ups, Grade Promotions, and Stat Point rewards."""
        player = await db.players.find_one({"_id": user_id})
        if not player: return

        current_xp = player.get("xp", 0) + xp_amount
        level = player.get("level", 1)
        xp_needed = (level ** 2) * 100

        if current_xp >= xp_needed:
            new_level = level + 1
            old_grade = player.get("grade", "Grade 4 Sorcerer")
            new_grade = self.get_grade_from_level(new_level)
            
            # Update DB: Level up, reset XP overflow, set Grade, and grant 5 Stat Points
            await db.players.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "level": new_level, 
                        "xp": current_xp - xp_needed, 
                        "grade": new_grade
                    },
                    "$inc": {"stat_points": 5}
                }
            )
            
            # --- High Quality Level Up Embed ---
            embed = discord.Embed(
                title="✨ LIMIT BREAK: LEVEL UP",
                description=f"**{player['name']}**'s cursed energy has surged to new heights!",
                color=0xf1c40f # Gold
            )
            embed.add_field(name="📈 New Level", value=f"`{new_level}`", inline=True)
            embed.add_field(name="🎖️ New Rank", value=f"`{new_grade}`", inline=True)
            embed.add_field(name="💎 Rewards", value="`+5 Stat Points`", inline=False)
            
            # Special Grade Promotion Alert
            if new_grade == "Special Grade Sorcerer" and old_grade != "Special Grade Sorcerer":
                embed.title = "💀 CATEGORY: SPECIAL GRADE"
                embed.color = 0x000000 # Black
                BannerManager.apply(embed, type="combat")
                await channel.send(content="@everyone **ANOMALY DETECTED: A NEW SPECIAL GRADE HAS ASCENDED.**", embed=embed)
            else:
                BannerManager.apply(embed, type="combat")
                await channel.send(embed=embed)
        else:
            await db.players.update_one({"_id": user_id}, {"$set": {"xp": current_xp}})

    @commands.command(name="train")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def train(self, ctx):
        """Standard training command for XP grinding."""
        xp_gain = random.randint(50, 150)
        
        embed = discord.Embed(
            title="🥋 Dojo Training",
            description=f"You focused your cursed energy and gained **{xp_gain} XP**.",
            color=0x3498db
        )
        BannerManager.apply(embed, type="combat")
        await ctx.send(embed=embed)
        await self.add_xp(str(ctx.author.id), xp_gain, ctx.channel)

    # --- Admin Fighting Style Tools ---

    @app_commands.command(name="fighting_create", description="Admin: Create a new Fighting Style.")
    @is_admin()
    async def fighting_create(self, interaction: discord.Interaction, name: str, s1_name: str, s2_name: str, s3_name: str):
        style_data = {"name": name, "skills": {"1": s1_name, "2": s2_name, "3": s3_name}}
        await db.fighting_styles.update_one({"name": name}, {"$set": style_data}, upsert=True)
        
        embed = discord.Embed(title="👊 NEW STYLE REGISTERED", color=0x2ecc71)
        embed.add_field(name="Style Name", value=f"`{name}`", inline=False)
        embed.add_field(name="Skill 1", value=s1_name, inline=True)
        embed.add_field(name="Skill 2", value=s2_name, inline=True)
        embed.add_field(name="Skill 3", value=s3_name, inline=True)
        
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="fighting_skill_dmg", description="Admin: Set damage for style skills.")
    @is_admin()
    async def fighting_skill_dmg(self, interaction: discord.Interaction, style_name: str, s1_dmg: int, s2_dmg: int, s3_dmg: int):
        style = await db.fighting_styles.find_one({"name": style_name})
        if not style:
            return await interaction.response.send_message("❌ Fighting Style not found.", ephemeral=True)
            
        dmgs = [s1_dmg, s2_dmg, s3_dmg]
        for i, (slot, skill) in enumerate(style["skills"].items()):
            await db.db["skills_library"].update_one(
                {"name": skill}, 
                {"$set": {"damage": dmgs[i], "type": "fighting_style"}}, 
                upsert=True
            )
            
        embed = discord.Embed(title="⚡ COMBAT DATA UPDATED", description=f"Damage scales adjusted for **{style_name}**.", color=0xe67e22)
        embed.add_field(name="Skill 1 Dmg", value=f"`{s1_dmg}`", inline=True)
        embed.add_field(name="Skill 2 Dmg", value=f"`{s2_dmg}`", inline=True)
        embed.add_field(name="Skill 3 Dmg", value=f"`{s3_dmg}`", inline=True)
        
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(FightingCog(bot))
    
