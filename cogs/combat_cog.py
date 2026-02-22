import discord
from discord.ext import commands
from database.connection import db
from systems.damage_calc import calculate_final_damage
from utils.banner_manager import BannerManager

class CombatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_skill_data(self, name, move_num=None, is_ct=False):
        """Fetches skill data from the library."""
        if is_ct:
            return await db.skills.find_one({"move_title": name})
        return await db.skills.find_one({"name": name, "move_number": move_num})

    @commands.command(name="W")
    async def weapon_attack(self, ctx, move_num: int):
        """Standard Weapon Attack: !W 1, !W 2, or !W 3"""
        user_id = str(ctx.author.id)
        player = await db.players.find_one({"_id": user_id})
        
        # Logic to fetch equipped weapon (placeholder for equipment system)
        weapon_name = player.get("equipped_weapon", "Katana")
        skill = await self.get_skill_data(weapon_name, move_num)

        if not skill:
            return await ctx.send("❌ Move not found for this weapon.")

        dmg, crit = calculate_final_damage(player, skill)
        
        embed = discord.Embed(
            title=f"⚔️ {ctx.author.display_name} strikes with {weapon_name}!",
            description=f"Used **{skill['move_title']}** dealing **{dmg}** damage! {'**BLACK FLASH!**' if crit else ''}",
        )
        BannerManager.apply(embed, type="combat")
        await ctx.send(embed=embed)

    @commands.command(name="CE")
    async def technique_attack(self, ctx, *, skill_name: str):
        """Cursed Technique Attack: !CE [Skill Name]"""
        user_id = str(ctx.author.id)
        player = await db.players.find_one({"_id": user_id})
        
        skill = await self.get_skill_data(skill_name, is_ct=True)

        if not skill:
            return await ctx.send("❌ Cursed Technique move not found.")

        # CE Check
        if player['stats']['cur_ce'] < skill['ce_cost']:
            return await ctx.send("❌ Not enough Cursed Energy!")

        dmg, crit = calculate_final_damage(player, skill)
        
        # Deduct CE
        await db.players.update_one({"_id": user_id}, {"$inc": {"stats.cur_ce": -skill['ce_cost']}})

        embed = discord.Embed(
            title=f"🌀 {ctx.author.display_name} activates {skill['parent_ct']}!",
            description=f"**{skill_name}** deals **{dmg}** damage! {'**CRITICAL HIT!**' if crit else ''}",
        )
        BannerManager.apply(embed, type="combat")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CombatCog(bot))
    
