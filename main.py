import discord
from discord.ext import commands
import os
import asyncio
import logging
from config import TOKEN, MAIN_COLOR

# Setup Logging for errors
logging.basicConfig(level=logging.INFO)

class JJKBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        print("--- Initializing Cursed Energy ---")
        # Automatically load all cogs in the cogs folder
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f'Loaded Cog: {filename}')
        
        # Syncing Slash Commands
        await self.tree.sync()
        print("--- Domain Expansion: Slash Commands Synced ---")

    async def on_ready(self):
        await self.change_presence(
            activity=discord.Game(name="Jujutsu Kaisen RPG | /start")
        )
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print("Ready to exorcise Curses.")

bot = JJKBot()

# Global Error Handler
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"Slow down! Your Cursed Energy is depleted. Try again in {error.retry_after:.2f}s.", 
            ephemeral=True
        )
    else:
        print(f"Error: {error}")

if __name__ == "__main__":
    bot.run(TOKEN)
    
