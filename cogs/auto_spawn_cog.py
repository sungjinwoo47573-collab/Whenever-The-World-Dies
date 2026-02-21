import discord
from discord.ext import tasks, commands
from database.connection import db
import random
from utils.banner_manager import BannerManager

class AutoSpawnCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spawn_loop.start()

    def cog_unload(self):
        self.spawn_loop.cancel()

    @tasks.loop(minutes=4)
    async def spawn_loop(self):
        # 1. CHECK IF A BOSS ALREADY EXISTS
        active_boss = await db.world_bosses.find_one({"is_active": True})
        
        # 2. IF A BOSS EXISTS, DON'T DESPAWN OR RESPAWN. JUST EXIT THE LOOP.
        if active_boss:
            print(f"World Boss '{active_boss['name']}' is still active. Skipping spawn cycle.")
            return

        # 3. NO ACTIVE BOSS? PROCEED TO SPAWN A NEW ONE
        all_bosses = await db.world_boss_library.find({"is_world_boss": True}).to_list(length=100)
        if not all_bosses:
            return

        boss_data = random.choice(all_bosses)
        
        # Mark the new boss as active in the database
        await db.world_bosses.update_one(
            {"name": boss_data["name"]},
            {"$set": {
                "is_active": True,
                "current_hp": boss_data["hp"],
                "max_hp": boss_data["hp"]
            }},
            upsert=True
        )

        # 4. SEND THE SPAWN EMBED
        channel = self.bot.get_channel(YOUR_RAID_CHANNEL_ID) # Replace with your channel ID
        if channel:
            embed = discord.Embed(
                title="🚨 WORLD BOSS APPEARED!",
                description=(
                    f"**Name:** {boss_data['name']}\n"
                    f"**HP:** `{boss_data['hp']:,}`\n"
                    f"**Technique:** {boss_data['technique']}"
                ),
                color=0x9b59b6 # Purple
            )
            if "image_url" in boss_data and boss_data["image_url"].startswith("http"):
                embed.set_image(url=boss_data["image_url"])
            
            BannerManager.apply(embed, type="combat")
            await channel.send(content="@everyone **A NEW THREAT HAS ARRIVED!**", embed=embed)

async def setup(bot):
    await bot.add_cog(AutoSpawnCog(bot))
    
