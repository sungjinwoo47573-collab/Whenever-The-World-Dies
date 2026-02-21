import discord
from discord.ext import commands, tasks
from database.connection import db
import random
import asyncio
from datetime import datetime, timedelta

class AutoSpawnCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_attack_time = {}
        self.active_boss_msg = None  # Stores the Discord Message object
        self.spawn_loop.start()

    def cog_unload(self):
        self.spawn_loop.cancel()

    @tasks.loop(minutes=10)
    async def spawn_loop(self):
        """Manifests a World Boss and cleans up old announcement messages."""
        config = await db.db["settings"].find_one({"setting": "wb_channel"})
        if not config:
            return

        target_channel_id = config.get("channel_id")
        channel = self.bot.get_channel(target_channel_id)
        if not channel:
            return

        # --- NEW: Cleanup Previous Message ---
        if self.active_boss_msg:
            try:
                await self.active_boss_msg.delete()
            except Exception as e:
                print(f"Cleanup failed (msg probably already deleted): {e}")
            self.active_boss_msg = None

        wb_pool = await db.npcs.find({"is_world_boss": True}).to_list(length=100)
        if not wb_pool:
            return

        boss = random.choice(wb_pool)
        boss_name = boss['name']
        
        await db.npcs.update_one({"name": boss_name}, {"$set": {"current_hp": boss["max_hp"]}})
        self.last_attack_time[boss_name] = datetime.utcnow()

        embed = discord.Embed(
            title="🚨 WORLD BOSS ALERT",
            description=f"**{boss_name}** has manifested!\n\n⚠️ *If no one attacks for 4 minutes, the boss will vanish.*",
            color=0xFF0000
        )
        if "image" in boss:
            embed.set_image(url=boss["image"])
        
        # Store the new message so we can delete it later
        self.active_boss_msg = await channel.send(content="@here **A NEW THREAT APPEARS!**", embed=embed)

        asyncio.create_task(self.monitor_boss_activity(channel, boss_name))

    async def monitor_boss_activity(self, channel, boss_name):
        """Checks if the boss has been ignored and despawns if necessary."""
        wb_cog = self.bot.get_cog("WorldBossCog")
        attack_task = asyncio.create_task(wb_cog.world_boss_attack_loop(channel, boss_name))

        while True:
            await asyncio.sleep(30)
            
            boss_data = await db.npcs.find_one({"name": boss_name})
            
            # If boss is defeated by players
            if not boss_data or boss_data['current_hp'] <= 0:
                if self.active_boss_msg:
                    try: await self.active_boss_msg.delete()
                    except: pass
                    self.active_boss_msg = None
                break

            # If boss is ignored for 4 minutes
            idle_duration = datetime.utcnow() - self.last_attack_time.get(boss_name, datetime.utcnow())
            if idle_duration > timedelta(minutes=4):
                attack_task.cancel()
                await db.npcs.update_one({"name": boss_name}, {"$set": {"current_hp": 0}})
                
                # Delete boss message on despawn
                if self.active_boss_msg:
                    try: await self.active_boss_msg.delete()
                    except: pass
                    self.active_boss_msg = None
                
                await channel.send(f"💨 **{boss_name}** vanished due to inactivity.", delete_after=10)
                break

    @commands.Cog.listener()
    async def on_message(self, message):
        """Resets the idle timer when someone uses a combat command."""
        if message.author.bot:
            return
        if any(message.content.startswith(p) for p in ["!CE", "!W", "!F", "!Domain"]):
            for boss_name in list(self.last_attack_time.keys()):
                self.last_attack_time[boss_name] = datetime.utcnow()

    @spawn_loop.before_loop
    async def before_spawn_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(AutoSpawnCog(bot))
    
