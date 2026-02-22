import discord
from discord.ext import commands
import random
import asyncio
from database.crud import get_player
from config import create_embed, MAIN_COLOR, BLACK_FLASH_CHANCE

class Combat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hit_count = {} # Tracking hits for guaranteed Black Flash
        self.cooldowns = commands.CooldownMapping.from_cooldown(1, 3.0, commands.BucketType.user)

    def check_black_flash(self, user_id):
        """Logic: 1/100 chance OR every 3rd hit is guaranteed."""
        if user_id not in self.hit_count:
            self.hit_count[user_id] = 0
        
        self.hit_count[user_id] += 1
        
        # Guaranteed on 3rd hit OR 1% random chance
        if self.hit_count[user_id] >= 3 or random.randint(1, 100) == 1:
            self.hit_count[user_id] = 0 # Reset after trigger
            return True
        return False

    async def execute_attack(self, ctx, type_label, slot):
        player = await get_player(ctx.author.id)
        if not player:
            return await ctx.send("You haven't started your journey yet! Use `/start`.")

        # Check for Black Flash
        is_black_flash = self.check_black_flash(ctx.author.id)
        
        # Calculate Base Damage (DMG stat + random variance)
        base_dmg = player.get('dmg', 10)
        final_dmg = random.randint(base_dmg, int(base_dmg * 1.2))
        
        if is_black_flash:
            final_dmg *= 2.5 # 2.5x Multiplier for Black Flash
            title = "✨ BLACK FLASH!"
            color = 0x000000 # Black color for impact
            desc = f"**{ctx.author.display_name}** experienced the sparks of black!\n**Damage:** {final_dmg}"
        else:
            title = f"⚔️ {type_label} Attack"
            color = MAIN_COLOR
            desc = f"**{ctx.author.display_name}** used **{type_label} Slot {slot}**!\n**Damage:** {final_dmg}"

        embed = create_embed(title, desc, color=color, user=ctx.author)
        await ctx.send(embed=embed)

    @commands.command(name="CT")
    async def cursed_technique(self, ctx, slot: int):
        """Usage: !CT 1-4"""
        if 1 <= slot <= 4:
            await self.execute_attack(ctx, "Cursed Technique", slot)

    @commands.command(name="F")
    async def fighting_style(self, ctx, slot: int):
        """Usage: !F 1-3"""
        if 1 <= slot <= 3:
            await self.execute_attack(ctx, "Fighting Style", slot)

    @commands.command(name="W")
    async def weapon(self, ctx, slot: int):
        """Usage: !W 1-4"""
        if 1 <= slot <= 4:
            await self.execute_attack(ctx, "Weapon", slot)

async def setup(bot):
    await bot.add_cog(Combat(bot))
  
