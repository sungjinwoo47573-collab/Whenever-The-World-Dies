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
        self.spawn_lock = False # Critical: Prevents double-spawning
        self.spawn_loop.start()

    def cog_unload(self):
        self.spawn_loop.cancel()

    @tasks.loop(minutes=10)
    async def spawn_loop(self):
        """Manifests a World Boss with high-quality UI and persistent logic."""
        if self.spawn_lock:
            return
        
        # 1. Get Channel Config
        config = await db.db["settings"].find_one({"setting": "wb_channel"})
        if not config:
            print("⚠️ World Boss channel not set in DB!")
            return

        channel = self.bot.get_channel(config.get("channel_id"))
        if not channel:
            return

        # 2. Check if a boss is ALREADY active (Prevents the 'Spam' look)
        active_check = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})
        if active_check:
            # If a boss is alive, we don't spawn a new one. We just update the message if needed.
            return

        self.spawn_lock = True

        # 3. Cleanup Previous Announcement
        if self.active_boss_msg:
            try:
                await self.active_boss_msg.delete()
            except:
                pass
            self.active_boss_msg = None

        # 4. Pick Boss from Pool
        wb_pool = await db.npcs.find({"is_world_boss": True}).to_list(length=100)
        if not wb_pool:
            self.spawn_lock = False
            return

        boss = random.choice(wb_pool)
        boss_name = boss['name']
        
        # Reset Boss HP in DB
        await db.npcs.update_one({"name": boss_name}, {"$set": {"current_hp": boss["max_hp"]}})
        self.last_attack_time[boss_name] = datetime.utcnow()

        # 5. Create High-Quality Embed
        embed = discord.Embed(
            title="🚨 SPECIAL GRADE THREAT DETECTED",
            description=(
                f"**Entity:** `{boss_name}`\n"
                f"**Status:** `Manifested`\n"
                f"**HP:** `{boss['max_hp']:,}`\n\n"
                "⚠️ *The boss will vanish if ignored for 4 minutes.*"
            ),
            color=0xFF0000
        )
        
        if "image" in boss:
            embed.set_image(url=boss["image"])
        elif "image_url" in boss:
             embed.set_image(url=boss["image_url"])

        # Apply the Professional Banner
        BannerManager.apply(embed, type="combat")
        
        self.active_boss_msg = await channel.send(content="@here **ANOMALY DETECTED IN THE CURTAIN!**", embed=embed)

        # 6. Start the Monitor and release lock
        asyncio.create_task(self.monitor_boss_activity(channel, boss_name))
        self.spawn_lock = False

    async def monitor_boss_activity(self, channel, boss_name):
        """Checks if the boss has been ignored and despawns if necessary."""
        # Note: Ensure WorldBossCog handles the actual attack logic
        wb_cog = self.bot.get_cog("WorldBossCog")
        
        attack_task = None
        if wb_cog:
            attack_task = asyncio.create_task(wb_cog.world_boss_attack_loop(channel, boss_name))

        while True:
            await asyncio.sleep(20)
            
            boss_data = await db.npcs.find_one({"name": boss_name})
            
            # Case 1: Boss is defeated
            if not boss_data or boss_data.get('current_hp', 0) <= 0:
                if self.active_boss_msg:
                    try: await self.active_boss_msg.delete()
                    except: pass
                    self.active_boss_msg = None
                break

            # Case 2: Boss is ignored (Despawn)
            idle_duration = datetime.utcnow() - self.last_attack_time.get(boss_name, datetime.utcnow())
            if idle_duration > timedelta(minutes=4):
                if attack_task:
                    attack_task.cancel()
                
                await db.npcs.update_one({"name": boss_name}, {"$set": {"current_hp": 0}})
                
                if self.active_boss_msg:
                    try: await self.active_boss_msg.delete()
                    except: pass
                    self.active_boss_msg = None
                
                exit_embed = discord.Embed(description=f"💨 **{boss_name}** has retreated into the shadows.", color=0x2b2d31)
                await channel.send(embed=exit_embed, delete_after=15)
                break

    @commands.Cog.listener()
    async def on_message(self, message):
        """Resets the idle timer when someone uses a combat command."""
        if message.author.bot:
            return
        # Added both Slash and Prefix support for reset
        content = message.content.upper()
        if any(content.startswith(p) for p in ["!CE", "!W", "!F", "/COMBAT", "/ATTACK"]):
            for boss_name in list(self.last_attack_time.keys()):
                self.last_attack_time[boss_name] = datetime.utcnow()

    @spawn_loop.before_loop
    async def before_spawn_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(AutoSpawnCog(bot))
        
