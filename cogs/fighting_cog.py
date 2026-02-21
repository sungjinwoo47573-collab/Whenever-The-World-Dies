import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.checks import is_admin
import random
import math

class FightingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- 📈 PROGRESSION LOGIC ---
    
    async def add_xp(self, user_id, xp_amount, channel):
        """Award XP and 5 Stat Points on Level Up."""
        player = await db.players.find_one({"_id": user_id})
        if not player:
            return

        current_xp = player.get("xp", 0) + xp_amount
        level = player.get("level", 1)
        xp_needed = (level ** 2) * 100

        if current_xp >= xp_needed:
            new_level = level + 1
            leftover_xp = current_xp - xp_needed
            
            # Atomic update: Level up and grant 5 points
            await db.players.update_one(
                {"_id": user_id},
                {
                    "$set": {"level": new_level, "xp": leftover_xp},
                    "$inc": {"stat_points": 5}
                }
            )
            
            embed = discord.Embed(
                title="🎊 LEVEL UP!",
                description=f"Congratulations! You've reached **Level {new_level}**.\n✨ **+5 Stat Points** awarded! Use `/distribute` to spend them.",
                color=0xFFD700
            )
            await channel.send(content=f"<@{user_id}>", embed=embed)
        else:
            await db.players.update_one({"_id": user_id}, {"$set": {"xp": current_xp}})

    @commands.command(name="train")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def train(self, ctx):
        """Standard command for players to grind XP."""
        xp_gain = random.randint(50, 150)
        await ctx.send(f"🥋 You spent an hour training your cursed energy. (+{xp_gain} XP)")
        await self.add_xp(str(ctx.author.id), xp_gain, ctx.channel)

    # --- 👊 FIGHTING STYLE ADMIN COMMANDS ---

    @app_commands.command(name="fighting_create", description="Admin: Create a new Fighting Style.")
    @is_admin()
    async def fighting_create(self, interaction: discord.Interaction, name: str, s1_name: str, s2_name: str, s3_name: str):
        style_data = {
            "name": name,
            "skills": {"1": s1_name, "2": s2_name, "3": s3_name}
        }
        await db.fighting_styles.update_one({"name": name}, {"$set": style_data}, upsert=True)
        await interaction.response.send_message(f"✅ **{name}** created with skills: {s1_name}, {s2_name}, {s3_name}.")

    @app_commands.command(name="fighting_skill_dmg", description="Admin: Set damage for style skills.")
    @is_admin()
    async def fighting_skill_dmg(self, interaction: discord.Interaction, style_name: str, s1_dmg: int, s2_dmg: int, s3_dmg: int):
        style = await db.fighting_styles.find_one({"name": style_name})
        if not style:
            return await interaction.response.send_message("❌ Fighting Style not found.", ephemeral=True)

        dmgs = [s1_dmg, s2_dmg, s3_dmg]
        for i, (slot, skill_name) in enumerate(style["skills"].items()):
            await db.db["skills_library"].update_one(
                {"name": skill_name},
                {"$set": {"damage": dmgs[i], "type": "fighting_style"}},
                upsert=True
            )
        await interaction.response.send_message(f"⚡ Damage values registered for **{style_name}**.")

    @app_commands.command(name="fighting_remove", description="Admin: Delete a fighting style.")
    @is_admin()
    async def fighting_remove(self, interaction: discord.Interaction, name: str):
        await db.fighting_styles.delete_one({"name": name})
        await interaction.response.send_message(f"🗑️ Fighting Style **{name}** has been removed.")

async def setup(bot):
    await bot.add_cog(FightingCog(bot))
    
