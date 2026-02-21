import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

class JJKBot(commands.Bot):
    def __init__(self):
        # Intents must be set to ALL to read message content for !CE/!F/!W commands
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None # Disabling default help to use our custom HelpCog
        )

    async def setup_hook(self):
        """Loads all Cogs and syncs Slash commands."""
        print("--- ⛩️ Initializing Jujutsu System ---")
        
        # This loop finds every file in /cogs and loads it automatically
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"✅ Loaded: {filename}")
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")

        # This syncs the slash commands to Discord's API
        # Note: Your Railway logs showed a 429 error; this is normal for large syncs.
        await self.tree.sync()
        print("--- 🌀 Domain Expansion Complete ---")

    async def on_ready(self):
        await self.change_presence(
            activity=discord.Game(name="JJK RPG | /start")
        )
        print(f"Logged in as {self.user} (ID: {self.user.id})")

bot = JJKBot()

# --- Critical: Process Prefix Commands ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Leveling from Messages (Logic from progression.py)
    try:
        from systems.progression import add_xp
        await add_xp(message.guild, message.author.id, 5)
    except:
        pass

    # This line is REQUIRED to make !CE1, !F1, etc. work!
    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
    
