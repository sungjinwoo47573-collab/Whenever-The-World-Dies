import discord
from discord.ext import commands
from database.connection import db
from systems.combat import active_combats, check_black_flash, apply_black_flash, npc_auto_attack_loop
from utils.embeds import JJKEmbeds
import asyncio

class CombatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bots and messages without our prefixes
        if message.author.bot or not any(message.content.startswith(p) for p in ["!CE", "!F", "!W"]):
            return

        channel_id = message.channel.id
        # Only process if there is an active NPC in this channel
        if channel_id not in active_combats:
            return

        user_id = str(message.author.id)
        content = message.content.upper()
        
        # 1. Fetch Player and NPC data
        player = await db.players.find_one({"_id": user_id})
        combat_data = active_combats[channel_id]
        npc = combat_data["npc"]

        if not player:
            return await message.reply("❌ You haven't started your journey! Use `/start` first.")

        # 2. Determine Action and Base Damage
        action_name = "Basic Strike"
        base_dmg = player["stats"]["dmg"]

        if content.startswith("!CE"):
            action_name = "Cursed Technique" # In full version, map to player's tech name
            base_dmg *= 1.5 # Techniques deal 50% more dmg
        elif content.startswith("!W"):
            action_name = "Weapon Art"
            base_dmg *= 1.2

        # 3. BLACK FLASH LOGIC (2.5% Chance)
        is_black_flash = await check_black_flash()
        final_dmg = apply_black_flash(base_dmg) if is_black_flash else base_dmg
        
        # Apply 12s Entropy/Variance (from NPC perspective, it affects player output slightly too)
        final_dmg = int(final_dmg * combat_data.get("variance", 1.0))

        # 4. UPDATE COMBAT STATE (Aggro & NPC HP)
        # Add damage to player's aggro score
        current_aggro = combat_data["players"].get(user_id, 0)
        active_combats[channel_id]["players"][user_id] = current_aggro + final_dmg
        
        # Subtract HP from NPC
        npc["hp"] -= final_dmg

        # 5. UI RESPONSE
        embed = JJKEmbeds.combat_log(
            player_name=message.author.display_name,
            target_name=npc["name"],
            action=action_name,
            damage=final_dmg,
            is_black_flash=is_black_flash
        )
        await message.channel.send(embed=embed)

        # 6. TRIGGER NPC RETALIATION
        # If the NPC isn't already attacking, start the AI loop
        if not combat_data.get("ai_active"):
            active_combats[channel_id]["ai_active"] = True
            self.bot.loop.create_task(npc_auto_attack_loop(message, npc))

        # 7. WIN CONDITION
        if npc["hp"] <= 0:
            from systems.economy import distribute_rewards
            await message.channel.send(f"🎊 **{npc['name']}** has been exorcised!")
            await distribute_rewards(message, channel_id, npc)

    @commands.command(name="Domain")
    async def domain_expansion(self, ctx):
        """The ultimate move. Buffs stats and changes the channel visual."""
        await ctx.send(f"🤞 **DOMAIN EXPANSION!** {ctx.author.mention} has trapped the Curse in their inner world!")
        # Logic for stat buffs and CE burnout would go here

async def setup(bot):
    await bot.add_cog(CombatCog(bot))
  
