import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from database.connection import db

load_dotenv()

class JJKBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None 
        )

    async def setup_hook(self):
        print("--- ⛩️  Initializing Jujutsu Chronicles System ---")
        
        # FIX: Check to ignore __init__.py files during the cog loading loop
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and filename != "__init__.py":
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"✅ Loaded Cog: {filename}")
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")

        try:
            print("🔄 Syncing Slash Commands...")
            await self.tree.sync()
        except Exception as e:
            print(f"❌ Sync Error: {e}")

        print("--- 🌀 Domain Expansion Complete ---")

    async def on_ready(self):
        await self.change_presence(activity=discord.Game(name="JJK RPG | /start"))
        print(f"👤 Logged in as: {self.user.name}")

bot = JJKBot()

@bot.event
async def on_message(message):
    if message.author.bot: return
    try:
        from systems.progression import add_xp
        await add_xp(message.guild, message.author.id, 5)
    except: pass
    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
    
