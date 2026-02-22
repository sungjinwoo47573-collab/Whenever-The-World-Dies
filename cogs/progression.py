import discord
from discord.ext import commands
import time
from database.crud import update_xp
from config import create_embed, SUCCESS_COLOR, XP_PER_MESSAGE

class Progression(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {} # Prevents XP spamming (1 min cooldown per user)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bots and commands
        if message.author.bot or message.content.startswith('!'):
            return

        user_id = message.author.id
        current_time = time.time()

        # Chat XP Cooldown Logic (1 message every 60s counts for XP)
        if user_id in self.cooldowns:
            if current_time - self.cooldowns[user_id] < 60:
                return

        self.cooldowns[user_id] = current_time

        # Update XP in database
        result = await update_xp(user_id, XP_PER_MESSAGE)

        if result and result.get("leveled_up"):
            new_level = result["level"]
            new_grade = result["grade"]
            
            # High-quality Level Up notification
            embed = create_embed(
                "📈 PROMOTION", 
                f"Congratulations {message.author.mention}!\n"
                f"You have reached **Level {new_level}**.\n"
                f"Your standing has been updated to: **{new_grade}**.\n"
                f"You gained **3 Stat Points**! Use `/profile` to spend them.",
                color=SUCCESS_COLOR,
                user=message.author
            )
            await message.channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Progression(bot))
  
