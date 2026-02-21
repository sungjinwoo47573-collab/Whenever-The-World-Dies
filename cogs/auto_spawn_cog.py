import discord
from discord.ext import commands, tasks
from database.connection import db
import random
import asyncio

class AutoSpawnCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raid_channel_id = 123456789012345678  # ⚠️ Replace with your Raid Channel ID
        self.spawn_loop.start()

    def cog_unload(self):
        self.spawn_loop.cancel()

    @tasks.loop(minutes=10)
    async def spawn_loop(self):
        """Automatically selects and spawns a World Boss every 10 minutes."""
        # 1. Fetch all available World Bosses
        wb_pool = await db.npcs.find({"is_world_boss": True}).to_list(length=100)
        
        if not wb_pool:
            print("⚠️ Auto-Spawn: No World Bosses found in database.")
            return

        # 2. Pick a random boss and reset its HP
        boss = random.choice(wb_pool)
        boss_name = boss['name']
        await db.npcs.update_one(
            {"name": boss_name},
            {"$set": {"current_hp": boss["max_hp"]}}
        )

        # 3. Get the target channel
        channel = self.bot.get_channel(self.raid_channel_id)
        if not channel:
            print(f"⚠️ Auto-Spawn: Could not find channel {self.raid_channel_id}")
            return

        # 4. Broadcast the manifestation
        embed = discord.Embed(
            title="🚨 EMERGENCY: WORLD BOSS DETECTED",
            description=f"Cursed energy levels are spiking! **{boss_name}** has manifested.\n\n**Time to kill:** 10 Minutes until next rotation!",
            color=0xFF0000
        )
        embed.set_image(url=boss.get("image", ""))
        await channel.send(embed=embed)

        # 5. Start the Attack Loop from WorldBossCog
        wb_cog = self.bot.get_cog("WorldBossCog")
        if wb_cog:
            # We use create_task so the timer keeps running while the boss fights
            asyncio.create_task(wb_cog.world_boss_attack_loop(channel, boss_name))

    @spawn_loop.before_loop
    async def before_spawn_loop(self):
        """Wait for the bot to be ready before starting the timer."""
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(AutoSpawnCog(bot))
  
