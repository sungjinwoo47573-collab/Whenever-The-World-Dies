import discord
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager
import random
import asyncio

class CombatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def calculate_black_flash(self, damage):
        """Standard 1% chance for a 2.5x damage spike."""
        if random.random() < 0.01: # 1% Chance
            return int(damage * 2.5), True
        return damage, False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.content.startswith("!"):
            return

        content = message.content.upper()
        user_id = str(message.author.id)

        # Identification of the attack type
        category_map = {"!CE": "technique", "!F": "fighting_style", "!W": "weapon"}
        prefix = None
        for p in category_map.keys():
            if content.startswith(p):
                prefix = p
                break
        
        if not prefix:
            return

        # 1. Player & Boss Verification
        player = await db.players.find_one({"_id": user_id})
        # Check for any active boss or NPC in the database
        boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})

        if not player: return
        if not boss:
            return await message.reply("🌑 There is no active threat to strike.")

        # 2. Parsing move number (e.g., !CE 1)
        try:
            move_num = int(content.replace(prefix, "").strip())
        except ValueError:
            move_num = 1

        # 3. Loadout Check
        category = category_map[prefix]
        active_item = player.get("loadout", {}).get(category)

        if not active_item:
            return await message.reply(f"❌ You don't have a **{category.replace('_', ' ')}** equipped! Use `/equip`.")

        # 4. CE Cost (Only for Technique)
        if category == "technique":
            ce_cost = move_num * 15
            current_ce = player.get("stats", {}).get("current_ce", 0)
            if current_ce < ce_cost:
                return await message.reply(f"⚠️ Insufficient CE! Need `{ce_cost}`, you have `{current_ce}`.")
            await db.players.update_one({"_id": user_id}, {"$inc": {"stats.current_ce": -ce_cost}})

        # 5. Skill Data & Damage Calculation
        skill_data = await db.skills.find_one({"name": active_item, "move_number": move_num})
        if not skill_data:
            return await message.reply(f"❌ Move `{move_num}` for **{active_item}** is not registered.")

        base_dmg = skill_data.get("damage", 0)
        player_dmg_stat = player.get("stats", {}).get("dmg", 10)
        
        # Apply 2-5% Player Variance
        player_variance = random.uniform(0.98, 1.05)
        total_dmg = int((base_dmg + player_dmg_stat) * player_variance)
        
        # Black Flash!
        final_dmg, is_bf = self.calculate_black_flash(total_dmg)

        # 6. Apply Damage to Boss
        new_hp = max(0, boss["current_hp"] - final_dmg)
        await db.npcs.update_one({"_id": boss["_id"]}, {"$set": {"current_hp": new_hp}})

        # 7. UI Combat Log
        rarity = skill_data.get("rarity", "Common")
        colors = {"Common": 0x95a5a6, "Rare": 0x3498db, "Epic": 0x9b59b6, "Legendary": 0xf1c40f, "Special Grade": 0xe74c3c}
        
        embed = discord.Embed(
            title=f"💥 {'BLACK FLASH!' if is_bf else 'CRITICAL STRIKE!'}",
            description=f"**{player['name']}** uses **{skill_data.get('move_title', active_item)}**!\n"
                        f"Target: **{boss['name']}**\n"
                        f"Damage: `{final_dmg:,}`",
            color=0x000000 if is_bf else colors.get(rarity, 0x2b2d31)
        )
        if is_bf: embed.set_footer(text="The sparks of black do not choose who to bless.")
        BannerManager.apply(embed, type="combat")
        await message.channel.send(embed=embed)

        # 8. Trigger Reactive Counter
        # This calls the Boss Retaliation logic directly from the WorldBossCog
        wb_cog = self.bot.get_cog("WorldBossCog")
        if wb_cog and new_hp > 0:
            # We update the local boss object for the retaliation function
            boss["current_hp"] = new_hp 
            await asyncio.sleep(1.5)
            await wb_cog.boss_retaliation(message.channel, boss)
        elif new_hp <= 0:
            if boss.get("phase") == 1:
                await wb_cog.trigger_phase_two(message.channel, boss)
            else:
                await message.channel.send(f"🎊 **{boss['name']}** has been exorcised by **{player['name']}**!")

async def setup(bot):
    await bot.add_cog(CombatCog(bot))
            
