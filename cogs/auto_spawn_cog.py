import discord
from discord.ext import commands, tasks
from database.connection import db
import random
import asyncio
from datetime import datetime, timedelta

class AutoSpawnCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_attack_time = {} # Track last attack per boss/channel
        self.spawn_loop.start()

    def cog_unload(self):
        self.spawn_loop.cancel()

    @tasks.loop(minutes=10)
    async def spawn_loop(self):
        """Manifests a World Boss and monitors for inactivity."""
        config = await db.db["settings"].find_one({"setting": "wb_channel"})
        if not config:
            return

        target_channel_id = config.get("channel_id")
        channel = self.bot.get_channel(target_channel_id)
        if not channel:
            return

        wb_pool = await db.npcs.find({"is_world_boss": True}).to_list(length=100)
        if not wb_pool:
            return

        boss = random.choice(wb_pool)
        boss_name = boss['name']
        
        # Reset Boss HP and set initial activity time
        await db.npcs.update_one({"name": boss_name}, {"$set": {"current_hp": boss["max_hp"]}})
        self.last_attack_time[boss_name] = datetime.utcnow()

        embed = discord.Embed(
            title="🚨 WORLD BOSS ALERT",
            description=f"**{boss_name}** has manifested!\n\n⚠️ *If no one attacks for 4 minutes, the boss will vanish.*",
            color=0xFF0000
        )
        if "image" in boss:
            embed.set_image(url=boss["image"])
        await channel.send(embed=embed)

        # Start the specialized monitoring loop
        asyncio.create_task(self.monitor_boss_activity(channel, boss_name))

    async def monitor_boss_activity(self, channel, boss_name):
        """Checks every 30 seconds if the boss has been ignored."""
        wb_cog = self.bot.get_cog("WorldBossCog")
        
        # Start the attack loop
        attack_task = asyncio.create_task(wb_cog.world_boss_attack_loop(channel, boss_name))

        while True:
            await asyncio.sleep(30) # Check frequency
            
            # Check if boss is dead
            boss_data = await db.npcs.find_one({"name": boss_name})
            if not boss_data or boss_data['current_hp'] <= 0:
                break

            # Calculate idle time
            idle_duration = datetime.utcnow() - self.last_attack_time.get(boss_name, datetime.utcnow())
            
            if idle_duration > timedelta(minutes=4):
                # Despawn Logic
                attack_task.cancel() # Stop the boss from hitting players
                await db.npcs.update_one({"name": boss_name}, {"$set": {"current_hp": 0}})
                
                despawn_embed = discord.Embed(
                    title="💨 BOSS DESPAWNED",
                    description=f"**{boss_name}** grew bored of your cowardice and vanished into the shadows.",
                    color=0x333333
                )
                await channel.send(embed=despawn_embed)
                break

    @commands.Cog.listener()
    async def on_message(self, message):
        """Updates the activity timer whenever a player uses a combat command."""
        if message.author.bot:
            return
            
        # If the player uses any of your combat prefixes
        if any(message.content.startswith(p) for p in ["!CE", "!W", "!F", "!Domain"]):
            # For simplicity, we update the timer for all active bosses in that channel
            for boss_name in self.last_attack_time:
                self.last_attack_time[boss_name] = datetime.utcnow()

    @spawn_loop.before_loop
    async def before_spawn_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(AutoSpawnCog(bot))
    
