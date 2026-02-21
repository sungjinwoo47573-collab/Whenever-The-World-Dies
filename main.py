import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

class JJKBot(commands.Bot):
    def __init__(self):
        # Intents are required for reading messages (!CE commands) and managing roles
        intents = discord.Intents.default()
        intents.message_content = True 
        intents.members = True          
        
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        """This runs before the bot starts to load all feature modules."""
        print("--- Initializing Jujutsu Systems ---")
        
        # Automatically load all .py files from the /cogs folder
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"✅ Loaded: {filename}")
                except Exception as e:
                    print(f"❌ Error loading {filename}: {e}")
        
        # Syncing Slash Commands (/) to Discord
        await self.tree.sync()
        print("⚡ Slash Commands Synchronized")

    async def on_ready(self):
        print(f"🔥 Logged in as: {self.user.name}")
        print(f"🆔 ID: {self.user.id}")
        print("--- Sorcerer Database Connected ---")

if __name__ == "__main__":
    bot = JJKBot()
    # Pulls token from the .env file
    bot.run(os.getenv("DISCORD_TOKEN"))
  
