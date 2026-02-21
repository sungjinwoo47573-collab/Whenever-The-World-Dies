import discord
from discord.ext import commands
from database.connection import db
from systems.combat import active_combats, get_black_flash, apply_effect, npc_ai_loop
from utils.embeds import JJKEmbeds
from utils.checks import handle_fatality
import random

class CombatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.content.startswith("!"):
            return

        content = message.content.upper()
        user_id = str(message.author.id)
        channel_id = message.channel.id

        # Check if combat is active in this channel
        if channel_id not in active_combats:
            return

        combat = active_combats[channel_id]
        player = await db.players.find_one({"_id": user_id})
        if not player: return

        prefix = ""
        slot = ""
        category = ""

        # Parse Prefix: !CE1-5, !F1-3, !W1-4
        if content.startswith("!CE"):
            prefix, category = "!CE", "technique"
            slot = content.replace("!CE", "")
        elif content.startswith("!F"):
            prefix, category = "!F", "fighting_style"
            slot = content.replace("!F", "")
        elif content.startswith("!W"):
            prefix, category = "!W", "weapon"
            slot = content.replace("!W", "")
        elif content == "!DOMAIN":
            return await self.handle_domain(message, player, combat)
        else:
            return

        # 1. Get the equipped item/tech name
        equipped_item = player["loadout"].get(category)
        if not equipped_item:
            return await message.reply(f"❌ You don't have a {category} equipped!")

        # 2. Find the skill name mapped to that slot
        source_data = None
        if category == "technique":
            source_data = await db.techniques.find_one({"name": equipped_item})
        elif category == "weapon":
            source_data = await db.items.find_one({"name": equipped_item})
        elif category == "fighting_style":
            source_data = await db.fighting_styles.find_one({"name": equipped_item})

        if not source_data or slot not in source_data.get("skills", {}):
            return await message.reply(f"❌ Skill slot {slot} is empty for {equipped_item}.")

        skill_name = source_data["skills"][slot]
        
        # 3. Fetch Skill Stats (DMG & Effects) from Skills Library
        skill_stats = await db.db["skills_library"].find_one({"name": skill_name})
        if not skill_stats:
            return await message.reply(f"❌ Skill data for **{skill_name}** not found in Library.")

        # 4. Calculation: Base + Player DMG Stat + Variance
        base_dmg = skill_stats["damage"]
        variance = combat.get("variance", 1.0)
        total_dmg = int((base_dmg + player["stats"]["dmg"]) * variance)

        # 5. Black Flash Check
        final_dmg, is_bf = get_black_flash(total_dmg)

        # 6. Apply Effects (Burn, Drain, etc.)
        effect_msg = await apply_effect("npc", channel_id, user_id, skill_stats.get("effect"), final_dmg)

        # 7. Update NPC HP and Player Aggro
        npc = combat["npc"]
        npc["hp"] -= final_dmg
        active_combats[channel_id]["players"][user_id] = active_combats[channel_id]["players"].get(user_id, 0) + final_dmg

        # UI Response
        embed = JJKEmbeds.combat_log(player["name"], npc["name"], skill_name, final_dmg, is_bf, effect_msg)
        await message.channel.send(embed=embed)

        # 8. Check if NPC is dead
        if npc["hp"] <= 0:
            from systems.economy import distribute_rewards
            rewards = await distribute_rewards(message, channel_id, npc)
            active_combats.pop(channel_id)
            await message.channel.send(f"🎊 **{npc['name']}** has been exorcised!")
            # Send reward summary here...

    async def handle_domain(self, message, player, combat):
        tech_name = player["loadout"].get("technique")
        tech_data = await db.techniques.find_one({"name": tech_name})
        
        if not tech_data or not tech_data.get("domain"):
            return await message.reply("❌ Your technique does not possess a Domain Expansion.")

        domain = tech_data["domain"]
        # Apply Buffs temporarily (Logic would track this in active_combats)
        await message.channel.send(f"🤞 **DOMAIN EXPANSION: {domain['name']}**\n{player['name']} receives massive stat buffs!")

async def setup(bot):
    await bot.add_cog(CombatCog(bot))
    
