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
        
        # --- RAID CONFIGURATION ---
        self.MAX_RAIDERS = 23  # Capacity increased to 23 players
        self.auto_spawn_loop.start()

    def cog_unload(self):
        self.auto_spawn_loop.cancel()

    # --- AUTO SPAWN LOOP (Every 10 Minutes) ---

    @tasks.loop(minutes=10)
    async def auto_spawn_loop(self):
        """Manifests a boss across all 6 sectors every 10 minutes."""
        config_chans = await db.db["settings"].find_one({"setting": "wb_channels"})
        if not config_chans or not config_chans.get("channel_ids"):
            return

        # Prevent overlapping spawns if a boss is still alive
        active_boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})
        if active_boss:
            return 

        boss_cursor = db.npcs.find({"is_world_boss": True})
        all_bosses = await boss_cursor.to_list(length=100)
        if not all_bosses:
            return
        
        selected_boss = random.choice(all_bosses)
        
        # Reset stats for the fresh global encounter
        await db.npcs.update_one(
            {"_id": selected_boss["_id"]},
            {"$set": {"current_hp": selected_boss["max_hp"], "phase": 1}}
        )

        embed = discord.Embed(
            title=f"🚨 THE VEIL DROPS: {selected_boss['name'].upper()}",
            description=(
                f"A Special Grade entity has manifested across all sectors!\n\n"
                f"**Global HP:** `{selected_boss['max_hp']:,}`\n"
                f"**Raid Capacity:** `{self.MAX_RAIDERS}` per sector.\n\n"
                "**BATTLE PROTOCOL:**\n"
                "• All damage is synced across all 6 channels.\n"
                "• Hit 0 HP = 10s Soul Lockout.\n"
                "• Reach 3 KOs for a guaranteed **Black Flash**."
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

    def get_hp_visuals(self, current, max_hp, phase=1):
        if max_hp <= 0: return "`[⬛⬛⬛⬛⬛]`", 0x000000, "DEAD"
        perc = (current / max_hp) * 100
        filled = max(0, min(10, int(perc / 10)))
        bar_emoji = "🟩" if phase == 1 else "🟥"
        return f"`{bar_emoji * filled}{'⬛' * (10-filled)}` **{perc:.1f}%**", 0, "LIVE"

    async def handle_player_death(self, ctx, member: discord.Member):
        user_id = str(member.id)
        if user_id in self.aggro_list:
            self.aggro_list.remove(user_id) # Free slot for 23rd+ players
        
        self.revenge_meter[user_id] = self.revenge_meter.get(user_id, 0) + 1
        
        try:
            await ctx.channel.set_permissions(member, send_messages=False)
            await ctx.send(f"💀 **{member.mention} has fallen!** A raid slot has opened. (10s Lockout)")
            await asyncio.sleep(10)
            await ctx.channel.set_permissions(member, overwrite=None)
            await db.players.update_one({"_id": user_id}, {"$set": {"stats.current_hp": 100}})
            await ctx.send(f"❤️ **{member.mention}** has returned.", delete_after=5)
        except: pass

    async def boss_retaliation(self, ctx, boss):
        if not self.aggro_list: return
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

        hp_bar, _, _ = self.get_hp_visuals(boss['current_hp'], boss['max_hp'], boss.get('phase', 1))
        await ctx.send(f"**{boss['name']} Retaliates!**\n{hp_bar}")

    async def execute_attack(self, ctx, category, move_num):
        user_id = str(ctx.author.id)
        player = await db.players.find_one({"_id": user_id})
        boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})

        if not player or not boss: return

        # Capacity check with new 23 limit
        if user_id not in self.aggro_list:
            if len(self.aggro_list) >= self.MAX_RAIDERS:
                return await ctx.send(f"🚫 **Raid is Full!** ({self.MAX_RAIDERS}/{self.MAX_RAIDERS})", delete_after=5)
            self.aggro_list.add(user_id)

        if player['stats']['current_hp'] <= 0: return

        loadout_key = {"CE": "technique", "W": "weapon", "F": "fighting_style"}[category]
        item_name = player.get("loadout", {}).get(loadout_key)
        skill = await db.skills.find_one({"name": item_name, "move_number": move_num})
        if not skill: return

        # Cooldown & CE Logic
        cd_key = f"{user_id}_{item_name}_{move_num}"
        now = datetime.utcnow()
        if cd_key in self.cooldowns and now < self.cooldowns[cd_key]:
            return await ctx.send("⏳ Cooldown!", delete_after=1)
        
        self.cooldowns[cd_key] = now + timedelta(seconds=skill.get("cooldown", 3))

        # Damage + Revenge System
        dmg_calc = (player['stats']['dmg'] + skill.get("damage", 0)) * random.uniform(0.98, 1.05)
        final_dmg = int(dmg_calc * 2.5) if self.revenge_meter.get(user_id, 0) >= 3 else int(dmg_calc)
        if self.revenge_meter.get(user_id, 0) >= 3: self.revenge_meter[user_id] = 0

        new_hp = max(0, boss['current_hp'] - final_dmg)
        await db.npcs.update_one({"_id": boss["_id"]}, {"$set": {"current_hp": new_hp}})
        
        await ctx.send(f"⚔️ **{ctx.author.name}** strikes **{boss['name']}**! (`-{final_dmg:,}` HP)")

        if new_hp > 0:
            await asyncio.sleep(1.2)
            boss['current_hp'] = new_hp
            await self.boss_retaliation(ctx, boss)
        else:
            self.aggro_list.clear()
            await ctx.send(f"🎊 **{boss['name']} has been EXORCISED!**")

    # --- PREFIX COMMANDS ---
    @commands.command(name="CE")
    async def ce(self, ctx, m: int = 1): await self.execute_attack(ctx, "CE", m)
    @commands.command(name="W")
    async def w(self, ctx, m: int = 1): await self.execute_attack(ctx, "W", m)
    @commands.command(name="F")
    async def f(self, ctx, m: int = 1): await self.execute_attack(ctx, "F", m)

async def setup(bot):
    await bot.add_cog(WorldBossCog(bot))
        
