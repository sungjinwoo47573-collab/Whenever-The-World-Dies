import discord
from discord.ext import commands, tasks
from database.connection import db
import random
import asyncio
import uuid
from datetime import datetime, timedelta
from utils.banner_manager import BannerManager

class AutoSpawnCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_session = None
        self.active_msg = None
        self.spawn_loop.start()

    def cog_unload(self):
        self.spawn_loop.cancel()

    @tasks.loop(minutes=10)
    async def spawn_loop(self):
        """The only authorized loop for spawning bosses."""
        # 1. GENERATE NEW SESSION ID
        self.active_session = str(uuid.uuid4())
        current_id = self.active_session

        # 2. CHECK FOR CHANNEL
        config = await db.db["settings"].find_one({"setting": "wb_channel"})
        if not config: return
        channel = self.bot.get_channel(config.get("channel_id"))
        if not channel: return

        # 3. PREVENT OVERLAP
        # Only spawn if the previous boss is marked as dead (current_hp <= 0)
        active_check = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})
        if active_check:
            print(f"[{datetime.now()}] Boss {active_check['name']} is still active. Skipping.")
            return

        # 4. PICK AND RESET BOSS
        pool = await db.npcs.find({"is_world_boss": True}).to_list(length=100)
        if not pool: return
        boss = random.choice(pool)
        
        await db.npcs.update_one({"_id": boss["_id"]}, {"$set": {"current_hp": boss["max_hp"]}})

        # 5. CLEANUP PREVIOUS MESSAGE
        if self.active_msg:
            try: await self.active_msg.delete()
            except: pass

        # 6. HIGH-QUALITY ANNOUNCEMENT
        embed = discord.Embed(
            title="⚠️ SPECIAL GRADE WARNING",
            description=f"**{boss['name']}** has materialized in the physical realm.\n\n*Idle duration: 4 minutes.*",
            color=0x9b59b6
        )
        if "image" in boss: embed.set_image(url=boss["image"])
        BannerManager.apply(embed, type="combat")
        
        self.active_msg = await channel.send(content="@everyone **A NEW CURSE HAS MANIFESTED!**", embed=embed)

        # 7. LAUNCH PROTECTED MONITOR
        asyncio.create_task(self.monitor_lifecycle(channel, boss["_id"], current_id))

    async def monitor_lifecycle(self, channel, boss_id, session_id):
        """Monitors boss health and shuts down if the session is no longer active."""
        last_interact = datetime.utcnow()
        
        while True:
            # SHUTDOWN: If a new loop started, this old task must die.
            if self.active_session != session_id:
                return

            await asyncio.sleep(30)
            
            boss_data = await db.npcs.find_one({"_id": boss_id})
            
            # Case: Boss Defeated
            if not boss_data or boss_data.get("current_hp", 0) <= 0:
                if self.active_msg:
                    try: await self.active_msg.delete()
                    except: pass
                    self.active_msg = None
                return

            # Case: Idle Timeout (4 Minutes)
            # You can update 'last_interact' in an on_message listener if desired
            if datetime.utcnow() - last_interact > timedelta(minutes=4):
                await db.npcs.update_one({"_id": boss_id}, {"$set": {"current_hp": 0}})
                if self.active_msg:
                    try: await self.active_msg.delete()
                    except: pass
                await channel.send(f"💨 The presence of the curse has faded...", delete_after=10)
                return

async def setup(bot):
    await bot.add_cog(AutoSpawnCog(bot))
        
