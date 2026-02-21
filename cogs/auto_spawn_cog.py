import discord
from discord.ext import commands, tasks
from database.connection import db
import random
import asyncio
import uuid # For unique session tracking
from datetime import datetime, timedelta
from utils.banner_manager import BannerManager

class AutoSpawnCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_attack_time = {}
        self.active_boss_msg = None  
        self.current_session_id = None # Track the latest active boss task
        self.spawn_loop.start()

    def cog_unload(self):
        self.spawn_loop.cancel()

    @tasks.loop(minutes=10)
    async def spawn_loop(self):
        # 1. KILL PREVIOUS SESSIONS
        # Changing the ID tells any running background tasks to stop immediately.
        self.current_session_id = str(uuid.uuid4())
        this_session = self.current_session_id

        config = await db.db["settings"].find_one({"setting": "wb_channel"})
        if not config: return
        channel = self.bot.get_channel(config.get("channel_id"))
        if not channel: return

        # 2. DATABASE CHECK
        # If a boss is already alive and active, don't post a new one.
        active_check = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})
        if active_check:
            print(f"Boss {active_check['name']} still alive. Skipping spawn.")
            return

        # 3. CLEANUP OLD MESSAGE
        if self.active_boss_msg:
            try: await self.active_boss_msg.delete()
            except: pass

        # 4. PICK NEW BOSS
        wb_pool = await db.npcs.find({"is_world_boss": True}).to_list(length=100)
        if not wb_pool: return

        boss = random.choice(wb_pool)
        boss_name = boss['name']
        
        await db.npcs.update_one({"name": boss_name}, {"$set": {"current_hp": boss["max_hp"]}})
        self.last_attack_time[boss_name] = datetime.utcnow()

        # 5. SEND EMBED
        embed = discord.Embed(
            title="🚨 WORLD BOSS ALERT",
            description=f"**{boss_name}** has manifested!\n\n⚠️ *If ignored for 4 minutes, the boss vanishes.*",
            color=0xFF0000
        )
        if "image" in boss: embed.set_image(url=boss["image"])
        BannerManager.apply(embed, type="combat")
        
        self.active_boss_msg = await channel.send(content="@here", embed=embed)

        # 6. START MONITOR (Pass the session ID)
        asyncio.create_task(self.monitor_boss_activity(channel, boss_name, this_session))

    async def monitor_boss_activity(self, channel, boss_name, session_id):
        """Monitors boss and dies if a newer session starts."""
        while True:
            # SHUTDOWN CHECK: If a new spawn_loop started, kill THIS background task.
            if self.current_session_id != session_id:
                print(f"Old session {session_id} detected. Shutting down monitor.")
                return

            await asyncio.sleep(20)
            
            boss_data = await db.npcs.find_one({"name": boss_name})
            
            # If boss is dead
            if not boss_data or boss_data.get('current_hp', 0) <= 0:
                if self.active_boss_msg:
                    try: await self.active_boss_msg.delete()
                    except: pass
                    self.active_boss_msg = None
                return

            # If boss is idle (Despawn)
            idle_duration = datetime.utcnow() - self.last_attack_time.get(boss_name, datetime.utcnow())
            if idle_duration > timedelta(minutes=4):
                await db.npcs.update_one({"name": boss_name}, {"$set": {"current_hp": 0}})
                if self.active_boss_msg:
                    try: await self.active_boss_msg.delete()
                    except: pass
                    self.active_boss_msg = None
                
                await channel.send(f"💨 **{boss_name}** vanished.", delete_after=5)
                return

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        content = message.content.upper()
        if any(content.startswith(p) for p in ["!CE", "!W", "!F", "!DOMAIN"]):
            for boss_name in list(self.last_attack_time.keys()):
                self.last_attack_time[boss_name] = datetime.utcnow()

    @spawn_loop.before_loop
    async def before_spawn_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(AutoSpawnCog(bot))
               
