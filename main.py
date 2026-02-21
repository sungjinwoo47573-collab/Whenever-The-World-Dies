import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from database.connection import db

load_dotenv()

class JJKBot(commands.Bot):
    def __init__(self):
        # Setting up both Prefixes (!CE, !F, !W) and Slash Commands
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        """Initializes database and loads all command modules (Cogs)."""
        print("--- ⛩️ Initializing Jujutsu System ---")
        
        # Folder for commands
        cog_folder = "./cogs"
        if not os.path.exists(cog_folder):
            os.makedirs(cog_folder)

        # Loading Cog files
        for filename in os.listdir(cog_folder):
            if filename.endswith(".py") and filename != "__init__.py":
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"✅ Loaded: {filename}")
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")

        # Syncing Slash Commands
        await self.tree.sync()
        print("--- 🌀 Domain Expansion Complete (Bot Ready) ---")

    async def on_ready(self):
        await self.change_presence(
            activity=discord.Game(name="Jujutsu Kaisen RPG | /start")
        )
        print(f"Logged in as {self.user} (ID: {self.user.id})")

bot = JJKBot()

# --- Global Logic for Combat/Messages ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. Leveling from Messages
    from systems.progression import add_xp
    await add_xp(message.guild, message.author.id, 5) # 5 XP per message

    # 2. Process Commands (!CE, !F, !W)
    await bot.process_commands(message)

# Run the Bot
if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
    
