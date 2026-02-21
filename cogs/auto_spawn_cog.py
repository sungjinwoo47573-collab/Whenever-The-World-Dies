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
        # Emergency internal cooldown to stop 'every second' execution
        self.internal_cooldown = datetime.utcnow()
        self.spawn_loop.start()

    def cog_unload(self):
        self.spawn_loop.cancel()

    @tasks.loop(minutes=10)
    async def spawn_loop(self):
        """Manifests a World Boss with multiple layers of spam protection."""
        
        # --- LAYER 1: INTERNAL MEMORY GUARD ---
        # If this function was called less than 60 seconds ago, STOP.
        if (datetime.utcnow() - self.internal_cooldown).total_seconds() < 60:
            return
        self.internal_cooldown = datetime.utcnow()

        try:
            # --- LAYER 2: DATABASE LOCK ---
            # Checks a global lock to ensure no other 'zombie' bot processes are running.
            lock = await db.db["settings"].find_one({"setting": "global_wb_lock"})
            if lock and lock.get("active"):
                last_s = lock.get("timestamp", datetime.utcnow())
                if (datetime.utcnow() - last_s).total_seconds() < 300: # 5 min lock
                    return

            # Set the Lock
            await db.db["settings"].update_one(
                {"setting": "global_wb_lock"},
                {"$set": {"active": True, "timestamp": datetime.utcnow()}},
                upsert=True
            )

            # --- LAYER 3: CONFIG & CHANNEL ---
            config = await db.db["settings"].find_one({"setting": "wb_channel"})
            if not config: return
            
            channel = self.bot.get_channel(config.get("channel_id"))
            if not channel: return

            # --- LAYER 4: CLEANUP & SPAWN ---
            # Only spawn if no boss is currently alive in DB
            alive = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})
            if alive:
                await db.db["settings"].update_one({"setting": "global_wb_lock"}, {"$set": {"active": False}})
                return

            wb_pool = await db.npcs.find({"is_world_boss": True}).to_list(length=100)
            if not wb_pool: 
                await db.db["settings"].update_one({"setting": "global_wb_lock"}, {"$set": {"active": False}})
                return

            boss = random.choice(wb_pool)
            boss_name = boss['name']
            
            await db.npcs.update_one({"name": boss_name}, {"$set": {"current_hp": boss["max_hp"]}})
            self.last_attack_time[boss_name] = datetime.utcnow()

            # --- LAYER 5: HIGH QUALITY UI ---
            embed = discord.Embed(
                title="🚨 SPECIAL GRADE MANIFESTATION",
                description=f"**Entity:** `{boss_name}`\n**HP:** `{boss['max_hp']:,}`\n\n*Threat level is critical. Exorcise immediately.*",
                color=0xFF0000
            )
            if "image" in boss: embed.set_image(url=boss["image"])
            BannerManager.apply(embed, type="combat")
            
            self.active_boss_msg = await channel.send(content="@here", embed=embed)

            # --- LAYER 6: BACKGROUND MONITOR ---
            # We use a controlled task to monitor activity
            self.bot.loop.create_task(self.monitor_boss(channel, boss_name))

        except Exception as e:
            print(f"CRITICAL SPAWN ERROR: {e}")
        finally:
            # Release lock so it can run again in 10 minutes
            await db.db["settings"].update_one({"setting": "global_wb_lock"}, {"$set": {"active": False}})

    async def monitor_boss(self, channel, boss_name):
        """Monitors boss health and idle time."""
        while True:
            await asyncio.sleep(30) # Check every 30 seconds, not every 1 second.
            
            boss_data = await db.npcs.find_one({"name": boss_name})
            if not boss_data or boss_data.get('current_hp', 0) <= 0:
                if self.active_boss_msg:
                    try: await self.active_boss_msg.delete()
                    except: pass
                break

            # Despawn if idle 4 mins
            idle = datetime.utcnow() - self.last_attack_time.get(boss_name, datetime.utcnow())
            if idle > timedelta(minutes=4):
                await db.npcs.update_one({"name": boss_name}, {"$set": {"current_hp": 0}})
                if self.active_boss_msg:
                    try: await self.active_boss_msg.delete()
                    except: pass
                await channel.send(f"💨 **{boss_name}** disappeared.", delete_after=10)
                break

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        if any(message.content.upper().startswith(p) for p in ["!CE", "!W", "!F", "!DOMAIN"]):
            for boss_name in list(self.last_attack_time.keys()):
                self.last_attack_time[boss_name] = datetime.utcnow()

async def setup(bot):
    await bot.add_cog(AutoSpawnCog(bot))
            
