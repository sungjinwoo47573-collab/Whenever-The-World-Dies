import discord
from discord.ext import commands, tasks
from database.connection import db
import random
import asyncio
from datetime import datetime, timedelta
from utils.banner_manager import BannerManager

class AutoSpawnCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_attack_time = {}
        self.active_boss_msg = None 
        self.spawn_loop.start()

    def cog_unload(self):
        self.spawn_loop.cancel()

    @tasks.loop(minutes=10)
    async def spawn_loop(self):
        """Manifests a World Boss using a Global Database Lock to prevent spam."""
        
        # 1. ATOMIC LOCK CHECK
        # We try to 'claim' the spawn slot in the DB. 
        # If 'is_locked' is already True, this will fail to update, and we stop.
        lock_result = await db.db["settings"].find_one_and_update(
            {"setting": "spawn_lock"},
            {"$set": {"is_locked": True, "last_spawn": datetime.utcnow()}},
            upsert=True
        )
        
        # If it was already locked in the last 60 seconds, stop immediately.
        if lock_result and lock_result.get("is_locked") and \
           (datetime.utcnow() - lock_result.get("last_spawn", datetime.utcnow())).total_seconds() < 60:
            return

        # 2. CHANNEL CONFIG
        config = await db.db["settings"].find_one({"setting": "wb_channel"})
        if not config:
            await db.db["settings"].update_one({"setting": "spawn_lock"}, {"$set": {"is_locked": False}})
            return

        channel = self.bot.get_channel(config.get("channel_id"))
        if not channel:
            await db.db["settings"].update_one({"setting": "spawn_lock"}, {"$set": {"is_locked": False}})
            return

        # 3. CLEANUP OLD MESSAGE
        if self.active_boss_msg:
            try: await self.active_boss_msg.delete()
            except: pass

        # 4. SPAWN LOGIC
        wb_pool = await db.npcs.find({"is_world_boss": True}).to_list(length=100)
        if not wb_pool:
            await db.db["settings"].update_one({"setting": "spawn_lock"}, {"$set": {"is_locked": False}})
            return

        boss = random.choice(wb_pool)
        boss_name = boss['name']
        
        await db.npcs.update_one({"name": boss_name}, {"$set": {"current_hp": boss["max_hp"]}})
        self.last_attack_time[boss_name] = datetime.utcnow()

        # 5. UI EMBED
        embed = discord.Embed(
            title="🚨 WORLD BOSS ALERT",
            description=f"**{boss_name}** has manifested!\n\n⚠️ *If ignored for 4 minutes, the boss vanishes.*",
            color=0xFF0000
        )
        if "image" in boss: embed.set_image(url=boss["image"])
        BannerManager.apply(embed, type="combat")
        
        self.active_boss_msg = await channel.send(content="@here", embed=embed)

        # 6. MONITOR TASK
        asyncio.create_task(self.monitor_boss_activity(channel, boss_name))
        
        # Release lock after successful spawn
        await db.db["settings"].update_one({"setting": "spawn_lock"}, {"$set": {"is_locked": False}})

    async def monitor_boss_activity(self, channel, boss_name):
        """Monitors idle time and handles despawn."""
        while True:
            await asyncio.sleep(30)
            boss_data = await db.npcs.find_one({"name": boss_name})
            
            if not boss_data or boss_data.get('current_hp', 0) <= 0:
                break

            idle_duration = datetime.utcnow() - self.last_attack_time.get(boss_name, datetime.utcnow())
            if idle_duration > timedelta(minutes=4):
                await db.npcs.update_one({"name": boss_name}, {"$set": {"current_hp": 0}})
                if self.active_boss_msg:
                    try: await self.active_boss_msg.delete()
                    except: pass
                break

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        if any(message.content.upper().startswith(p) for p in ["!CE", "!W", "!F", "!DOMAIN"]):
            for boss_name in list(self.last_attack_time.keys()):
                self.last_attack_time[boss_name] = datetime.utcnow()

async def setup(bot):
    await bot.add_cog(AutoSpawnCog(bot))
                    
