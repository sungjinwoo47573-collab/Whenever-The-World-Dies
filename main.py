import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import logging
from dotenv import load_dotenv

# Import the database connection to verify heartbeat on startup
from database.connection import db

# Initialize environment variables
load_dotenv()

class JJKBot(commands.Bot):
    def __init__(self):
        # Intents.all() is required to read !CE/!F/!W messages and manage roles
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None # Using custom HelpCog instead
        )

    async def setup_hook(self):
        """Initializes the core systems and loads all extensions."""
        print("--- ⛩️  Initializing Jujutsu Chronicles System ---")
        
        # 1. Verify Database Connection
        is_alive = await db.ping()
        if is_alive:
            print("✅ Database Connection: SECURE")
        else:
            print("❌ Database Connection: FAILED. Check your MONGO_URI in .env")

        # 2. Automatic Cog Loader
        # Scans the /cogs folder for any .py files and loads them as extensions
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"📦 Loaded Cog: {filename}")
                except Exception as e:
                    print(f"⚠️  Failed to load {filename}: {e}")

        # 3. Global Slash Command Sync
        # This pushes your /commands to Discord's servers
        try:
            print("🔄 Syncing Slash Commands (This may take a moment)...")
            synced = await self.tree.sync()
            print(f"✨ Successfully synced {len(synced)} commands.")
        except discord.errors.HTTPException as e:
            if e.status == 429:
                print("⏳ Rate limited during sync. Commands will update shortly.")
            else:
                print(f"❌ Sync Error: {e}")

        print("--- 🌀 Domain Expansion Complete: Bot is Live ---")

    async def on_ready(self):
        """Triggered when the bot is fully logged in and connected."""
        status = discord.Game(name="JJK RPG | /start")
        await self.change_presence(activity=status)
        print(f"👤 Logged in as: {self.user.name}")
        print(f"🆔 ID: {self.user.id}")

# --- Global Bot Events & Error Handling ---

bot = JJKBot()

@bot.event
async def on_message(message):
    """Handles prefix commands and passive XP gain."""
    if message.author.bot:
        return

    # Passive XP Gain: Awards 5 XP per message (Sync with progression system)
    try:
        from systems.progression import add_xp
        # We pass message.guild to allow for automated role updates
        await add_xp(message.guild, message.author.id, 5)
    except Exception as e:
        # Silently fail if player doesn't have a profile yet
        pass

    # Crucial: This allows !CE, !W, and !F commands to work alongside Slash commands
    await bot.process_commands(message)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Global handler for Slash Command failures."""
    if isinstance(error, app_commands.errors.CheckFailure):
        # This handles cases where @has_profile or @not_in_combat fails
        return # The specific error message is already sent in utils/checks.py
    
    # Generic error fallback
    print(f"Logged Error: {error}")
    if not interaction.response.is_done():
        await interaction.response.send_message(
            "⚠️ An internal technique error occurred. Please try again later.", 
            ephemeral=True
        )

# --- Execution ---

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ FATAL: No DISCORD_TOKEN found in environment variables.")
    else:
        bot.run(token)
