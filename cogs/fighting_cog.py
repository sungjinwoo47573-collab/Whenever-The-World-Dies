import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
from utils.checks import is_admin
import random

class FightingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_grade_from_level(self, level):
        """Maps levels to Jujutsu Sorcerer Grades with updated naming."""
        if level >= 80: return "Special Grade"
        if level >= 60: return "Grade 1"
        if level >= 40: return "Grade 2"
        if level >= 20: return "Grade 3"
        return "Grade 4"

    async def add_xp(self, user_id, xp_amount, channel):
        """Standardized XP engine with Stat Point rewards and Rank-up alerts."""
        player = await db.players.find_one({"_id": user_id})
        if not player: return

        current_xp = player.get("xp", 0) + xp_amount
        level = player.get("level", 1)
        xp_needed = (level ** 2) * 100

        if current_xp >= xp_needed:
            new_level = level + 1
            old_grade = player.get("grade", "Grade 4")
            new_grade = self.get_grade_from_level(new_level)
            
            # Update DB: Level up, grant points, and refresh current HP/CE
            await db.players.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "level": new_level, 
                        "xp": current_xp - xp_needed, 
                        "grade": new_grade,
                        "stats.current_hp": player['stats']['max_hp'],
                        "stats.current_ce": player['stats']['max_ce']
                    },
                    "$inc": {"stat_points": 5}
                }
            )
            
            # --- High-Quality Progression Embed ---
            embed = discord.Embed(
                title="✨ LEVEL UP: CURSED ENERGY SURGE",
                description=f"**{player['name']}** has reached a new height of sorcery!",
                color=0xf1c40f
            )
            embed.add_field(name="📈 Level", value=f"`{level}` → `{new_level}`", inline=True)
            embed.add_field(name="🎖️ Rank", value=f"`{new_grade}`", inline=True)
            embed.add_field(name="💎 Rewards", value="`+5 Stat Points` | `HP/CE Refilled`", inline=False)
            
            if new_grade == "Special Grade" and old_grade != "Special Grade":
                embed.title = "💀 ASCENSION: SPECIAL GRADE"
                embed.color = 0x000000
                BannerManager.apply(embed, type="combat")
                await channel.send(content="@everyone **WARNING: A NEW SPECIAL GRADE HAS BEEN REGISTERED.**", embed=embed)
            else:
                BannerManager.apply(embed, type="main")
                await channel.send(embed=embed)
        else:
            await db.players.update_one({"_id": user_id}, {"$set": {"xp": current_xp}})

    @commands.command(name="train")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def train(self, ctx):
        """Safe training command to gain XP without World Boss risk."""
        xp_gain = random.randint(50, 150)
        
        embed = discord.Embed(
            title="🥋 Dojo Training",
            description=f"You refined your cursed energy control and gained **{xp_gain} XP**.",
            color=0x3498db
        )
        BannerManager.apply(embed, type="main")
        await ctx.send(embed=embed)
        await self.add_xp(str(ctx.author.id), xp_gain, ctx.channel)

    # --- ADMIN FIGHTING STYLE TOOLS ---

    @app_commands.command(name="fighting_create", description="Admin: Create and map moves for a Fighting Style.")
    @is_admin()
    async def fighting_create(self, interaction: discord.Interaction, name: str, 
                               s1_name: str, s1_dmg: int, 
                               s2_name: str, s2_dmg: int, 
                               s3_name: str, s3_dmg: int):
        """Creates a style and automatically populates the combat 'skills' collection."""
        
        # 1. Update Style Entry
        style_data = {"name": name, "skills_mapped": True}
        await db.fighting_styles.update_one({"name": name}, {"$set": style_data}, upsert=True)
        
        # 2. Map moves to !F1, !F2, !F3 in the skills collection
        moves = [
            {"move_number": 1, "name": name, "move_title": s1_name, "damage": s1_dmg},
            {"move_number": 2, "name": name, "move_title": s2_name, "damage": s2_dmg},
            {"move_number": 3, "name": name, "move_title": s3_name, "damage": s3_dmg}
        ]
        
        for move in moves:
            await db.skills.update_one(
                {"name": move["name"], "move_number": move["move_number"]},
                {"$set": move},
                upsert=True
            )

        embed = discord.Embed(title="👊 MARTIAL ARTS REGISTERED", description=f"The **{name}** style is now combat-ready.", color=0x2ecc71)
        embed.add_field(name="Techniques", value=f"1. {s1_name} ({s1_dmg} DMG)\n2. {s2_name} ({s2_dmg} DMG)\n3. {s3_name} ({s3_dmg} DMG)")
        BannerManager.apply(embed, type="admin")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(FightingCog(bot))
                                    
