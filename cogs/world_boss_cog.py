import discord
from discord.ext import commands, tasks
from database.connection import db
import asyncio
import random
from datetime import datetime, timedelta

class WorldBossCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rarities = {"Common": "⚪", "Rare": "🔵", "Epic": "🟣", "Legendary": "🟡", "Special Grade": "🔴"}
        self.cooldowns = {} 
        self.revenge_meter = {}
        self.aggro_list = set()
        
        # --- DOMAIN STATE ---
        self.is_boss_frozen = False
        self.frozen_until = None
        self.domain_owner = None
        
        # --- RAID CONFIGURATION ---
        self.MAX_RAIDERS = 23 
        self.auto_spawn_loop.start()

    def cog_unload(self):
        self.auto_spawn_loop.cancel()

    # --- AUTO SPAWN LOOP (Every 10 Minutes) ---

    @tasks.loop(minutes=10)
    async def auto_spawn_loop(self):
        config_chans = await db.db["settings"].find_one({"setting": "wb_channels"})
        if not config_chans or not config_chans.get("channel_ids"):
            return

        active_boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})
        if active_boss:
            return 

        boss_cursor = db.npcs.find({"is_world_boss": True})
        all_bosses = await boss_cursor.to_list(length=100)
        if not all_bosses:
            return
        
        selected_boss = random.choice(all_bosses)
        
        await db.npcs.update_one(
            {"_id": selected_boss["_id"]},
            {"$set": {
                "current_hp": selected_boss["max_hp"], 
                "phase": 1,
                "domain_count": 0,
                "is_domain_active": False
            }}
        )

        embed = discord.Embed(
            title=f"🚨 THE VEIL DROPS: {selected_boss['name'].upper()}",
            description=(
                f"**Global HP:** `{selected_boss['max_hp']:,}`\n"
                f"**Raid Capacity:** `{self.MAX_RAIDERS}` per sector.\n\n"
                "**BATTLE PROTOCOL:**\n"
                "• All damage is synced across all channels.\n"
                "• Use `!domain` to freeze the boss (2 mins).\n"
                "• Domain triggers at 10% HP (Expect Debuffs)."
            ),
            color=0xff0000
        )
        if selected_boss.get("image"):
            embed.set_image(url=selected_boss["image"])

        for channel_id in config_chans["channel_ids"]:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(embed=embed)

    @auto_spawn_loop.before_loop
    async def before_spawn(self):
        await self.bot.wait_until_ready()

    # --- COMBAT UTILITIES ---

    async def handle_player_death(self, ctx, member: discord.Member):
        user_id = str(member.id)
        if user_id in self.aggro_list:
            self.aggro_list.remove(user_id)
        
        self.revenge_meter[user_id] = self.revenge_meter.get(user_id, 0) + 1
        
        try:
            await ctx.channel.set_permissions(member, send_messages=False)
            await ctx.send(f"💀 **{member.mention} has fallen!** Slot opened. (10s Lockout)")
            await asyncio.sleep(10)
            await ctx.channel.set_permissions(member, overwrite=None)
            await db.players.update_one({"_id": user_id}, {"$set": {"stats.current_hp": 100}})
            await ctx.send(f"❤️ **{member.mention}** returned.", delete_after=5)
        except: pass

    async def trigger_domain(self, ctx, boss):
        if boss.get("domain_count", 0) >= boss.get("domain_max", 1):
            return

        await ctx.send(f"🌌 **{boss['name']} expands its Domain!**")
        
        targets = list(self.aggro_list)
        dmg = boss.get("domain_dmg", 500)
        for uid in targets:
            member = ctx.guild.get_member(int(uid))
            if member:
                await db.players.update_one({"_id": uid}, {"$inc": {"stats.current_hp": -dmg}})
                p = await db.players.find_one({"_id": uid})
                if p['stats']['current_hp'] <= 0:
                    self.bot.loop.create_task(self.handle_player_death(ctx, member))

        self.aggro_list.clear()
        await db.npcs.update_one(
            {"_id": boss["_id"]}, 
            {"$inc": {"domain_count": 1}, "$set": {"is_domain_active": True}}
        )
        await ctx.send("📉 **TERRITORY PRESSURE:** Players now deal less damage and have slower cooldowns!")

    async def boss_retaliation(self, ctx, boss):
        if not self.aggro_list or self.is_boss_frozen: return
        phase_mult = 2.5 if boss.get("phase", 1) == 2 else 1.0
        
        targets = list(self.aggro_list)
        for uid in targets:
            member = ctx.guild.get_member(int(uid))
            if not member: continue
            
            dmg = int(boss.get("base_dmg", 100) * phase_mult * random.uniform(0.9, 1.1))
            await db.players.update_one({"_id": uid}, {"$inc": {"stats.current_hp": -dmg}})
            p_data = await db.players.find_one({"_id": uid})
            
            if p_data.get("stats", {}).get("current_hp", 0) <= 0:
                self.bot.loop.create_task(self.handle_player_death(ctx, member))

        await ctx.send(f"💢 **{boss['name']}** retaliates against the raid party!")

    # --- PLAYER DOMAIN ---

    @commands.command(name="domain")
    async def player_domain(self, ctx):
        user_id = str(ctx.author.id)
        player = await db.players.find_one({"_id": user_id})
        boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})

        if not player or not boss:
            return await ctx.send("❌ No World Boss to target.")

        if player.get("stats", {}).get("cur_ce", 0) < 100:
            return await ctx.send("❌ Insufficient Cursed Energy (100 required).")

        if self.is_boss_frozen:
            return await ctx.send("⚠️ A Domain is already active!")

        # Activate
        self.is_boss_frozen = True
        self.domain_owner = user_id
        duration = 120 # 2 minutes
        self.frozen_until = datetime.utcnow() + timedelta(seconds=duration)
        await db.players.update_one({"_id": user_id}, {"$inc": {"stats.cur_ce": -100}})

        await ctx.send(f"🌀 **DOMAIN EXPANSION!** {ctx.author.name} has frozen **{boss['name']}** for 2 minutes!")

        # Domain Clash/Freeze Loop
        elapsed = 0
        while elapsed < duration and self.is_boss_frozen:
            await asyncio.sleep(10)
            elapsed += 10
            # 15% chance for Boss to attempt a Clash and break out
            if random.random() < 0.15:
                self.is_boss_frozen = False
                await ctx.send(f"💥 **DOMAIN CLASH!** {boss['name']} has shattered the player's domain early!")
                return

        self.is_boss_frozen = False
        await ctx.send(f"🧊 **{boss['name']}** is no longer frozen.")

    # --- MAIN ATTACK LOGIC ---

    async def execute_attack(self, ctx, category, move_num):
        user_id = str(ctx.author.id)
        player = await db.players.find_one({"_id": user_id})
        boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})

        if not player or not boss: return

        if user_id not in self.aggro_list:
            if len(self.aggro_list) >= self.MAX_RAIDERS:
                return await ctx.send(f"🚫 Raid Full!", delete_after=5)
            self.aggro_list.add(user_id)

        if player['stats']['current_hp'] <= 0: return

        # Penalties (Disabled if boss is frozen by player domain)
        penalty = 0
        if boss.get("is_domain_active") and not self.is_boss_frozen:
            penalty = random.uniform(0.07, 0.12)
        
        loadout_key = {"CE": "technique", "W": "weapon", "F": "fighting_style"}[category]
        item_name = player.get("loadout", {}).get(loadout_key)
        skill = await db.skills.find_one({"name": item_name, "move_number": move_num})
        if not skill: return

        cd_key = f"{user_id}_{item_name}_{move_num}"
        if cd_key in self.cooldowns and datetime.utcnow() < self.cooldowns[cd_key]:
            return await ctx.send("⏳ Cooldown!", delete_after=1)
        
        self.cooldowns[cd_key] = datetime.utcnow() + timedelta(seconds=skill.get("cooldown", 3) * (1+penalty))

        # Damage
        dmg_calc = (player['stats']['dmg'] + skill.get("damage", 0)) * random.uniform(0.95, 1.05) * (1-penalty)
        if self.revenge_meter.get(user_id, 0) >= 3:
            final_dmg = int(dmg_calc * 2.5)
            self.revenge_meter[user_id] = 0
            await ctx.send("✨ **BLACK FLASH!**")
        else:
            final_dmg = int(dmg_calc)

        new_hp = max(0, boss['current_hp'] - final_dmg)
        await db.npcs.update_one({"_id": boss["_id"]}, {"$set": {"current_hp": new_hp}})
        await ctx.send(f"⚔️ **{ctx.author.name}** deals `{final_dmg:,}` damage!")

        if new_hp <= 0:
            self.is_boss_frozen = False
            await db.npcs.update_one({"_id": boss["_id"]}, {"$set": {"current_hp": 0, "is_domain_active": False}})
            self.aggro_list.clear()
            await ctx.send(f"🎊 **{boss['name']} defeated!**")
        else:
            if not self.is_boss_frozen:
                if new_hp <= (boss['max_hp'] * 0.1) and not boss.get("is_domain_active"):
                    await self.trigger_domain(ctx, boss)
                else:
                    await asyncio.sleep(1)
                    await self.boss_retaliation(ctx, boss)
            else:
                await ctx.send("❄️ Boss is frozen and cannot counter.", delete_after=2)

    @commands.command(name="CE")
    async def ce(self, ctx, m: int = 1): await self.execute_attack(ctx, "CE", m)
    @commands.command(name="W")
    async def w(self, ctx, m: int = 1): await self.execute_attack(ctx, "W", m)
    @commands.command(name="F")
    async def f(self, ctx, m: int = 1): await self.execute_attack(ctx, "F", m)

async def setup(bot):
    await bot.add_cog(WorldBossCog(bot))
        
