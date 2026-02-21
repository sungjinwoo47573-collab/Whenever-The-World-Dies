import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.checks import is_admin
import random

class FightingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_grade_from_level(self, level):
        if level >= 80: return "Special Grade Sorcerer"
        if level >= 60: return "Grade 1 Sorcerer"
        if level >= 40: return "Grade 2 Sorcerer"
        if level >= 20: return "Grade 3 Sorcerer"
        return "Grade 4 Sorcerer"

    async def add_xp(self, user_id, xp_amount, channel):
        player = await db.players.find_one({"_id": user_id})
        if not player: return

        current_xp = player.get("xp", 0) + xp_amount
        level = player.get("level", 1)
        xp_needed = (level ** 2) * 100

        if current_xp >= xp_needed:
            new_level = level + 1
            old_grade = player.get("grade", "Grade 4 Sorcerer")
            new_grade = self.get_grade_from_level(new_level)
            
            await db.players.update_one(
                {"_id": user_id},
                {
                    "$set": {"level": new_level, "xp": current_xp - xp_needed, "grade": new_grade},
                    "$inc": {"stat_points": 5}
                }
            )
            
            # Special Grade Promotion Embed
            if new_grade == "Special Grade Sorcerer" and old_grade != "Special Grade Sorcerer":
                embed = discord.Embed(
                    title="💀 BEYOND HUMAN LIMITS",
                    description=f"Attention! <@{user_id}> has ascended to **SPECIAL GRADE**.\n\n*The world will never be the same.*",
                    color=0x000000
                )
                embed.set_image(url="https://i.imgur.com/your_epic_gif_here.gif") # Optional epic image
                await channel.send(content="@everyone", embed=embed)
            else:
                await channel.send(f"🎊 **LEVEL UP!** <@{user_id}> reached **Level {new_level}** ({new_grade})!")
        else:
            await db.players.update_one({"_id": user_id}, {"$set": {"xp": current_xp}})

    @commands.command(name="train")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def train(self, ctx):
        xp_gain = random.randint(50, 150)
        await ctx.send(f"🥋 Training complete. (+{xp_gain} XP)")
        await self.add_xp(str(ctx.author.id), xp_gain, ctx.channel)

    @app_commands.command(name="fighting_create")
    @is_admin()
    async def fighting_create(self, interaction: discord.Interaction, name: str, s1_name: str, s2_name: str, s3_name: str):
        style_data = {"name": name, "skills": {"1": s1_name, "2": s2_name, "3": s3_name}}
        await db.fighting_styles.update_one({"name": name}, {"$set": style_data}, upsert=True)
        await interaction.response.send_message(f"✅ Style **{name}** created.")

    @app_commands.command(name="fighting_skill_dmg")
    @is_admin()
    async def fighting_skill_dmg(self, interaction: discord.Interaction, style_name: str, s1_dmg: int, s2_dmg: int, s3_dmg: int):
        style = await db.fighting_styles.find_one({"name": style_name})
        if not style: return await interaction.response.send_message("❌ Not found.")
        dmgs = [s1_dmg, s2_dmg, s3_dmg]
        for i, (slot, skill) in enumerate(style["skills"].items()):
            await db.db["skills_library"].update_one({"name": skill}, {"$set": {"damage": dmgs[i]}}, upsert=True)
        await interaction.response.send_message(f"⚡ Damage set for {style_name}.")

async def setup(bot):
    await bot.add_cog(FightingCog(bot))
                                                                                
