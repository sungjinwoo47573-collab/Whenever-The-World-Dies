import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
import asyncio
import random
from utils.banner_manager import BannerManager

class WorldBossCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Dictionary to track damage per boss session: {user_id: damage_dealt}
        self.damage_tracker = {}

    def generate_hp_bar(self, current, max_val, length=10, is_player=False):
        """Generates a high-quality health bar for both Boss and Players."""
        percentage = max(0, min(1, current / max_val))
        filled = int(percentage * length)
        
        if is_player:
            # Player bar is blue/white for clarity
            bar = "🟦" * filled + "⬜" * (length - filled)
        else:
            # Boss bar uses phase colors (handled in the command)
            bar = "▰" * filled + "▱" * (length - filled)
        
        return f"{bar} `{current:,}/{max_val:,} ({percentage:.1%})`"

    @app_commands.command(name="attack", description="Engage the active World Boss.")
    async def attack(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        # 1. FETCH DATA
        player = await db.players.find_one({"_id": user_id})
        boss = await db.npcs.find_one({"is_world_boss": True, "current_hp": {"$gt": 0}})

        if not player:
            return await interaction.response.send_message("❌ No profile found. Use `/start`.", ephemeral=True)
        if not boss:
            return await interaction.response.send_message("🌑 The area is quiet. No World Boss active.", ephemeral=True)

        # 2. DAMAGE CALCULATION
        p_stats = player.get("stats", {})
        p_hp = p_stats.get("current_hp", 100)
        p_max_hp = p_stats.get("max_hp", 100)
        
        if p_hp <= 0:
            return await interaction.response.send_message("💀 You are incapacitated! You cannot attack until you heal.", ephemeral=True)

        base_dmg = p_stats.get("dmg", 10)
        actual_dmg = int(base_dmg * random.uniform(0.85, 1.25)) # Critical hit variance
        
        # 3. UPDATE DATABASE (Boss HP & Damage Tracker)
        new_boss_hp = max(0, boss["current_hp"] - actual_dmg)
        await db.npcs.update_one({"_id": boss["_id"]}, {"$set": {"current_hp": new_boss_hp}})
        
        # Track damage for rewards
        self.damage_tracker[user_id] = self.damage_tracker.get(user_id, 0) + actual_dmg

        # 4. PHASE & HP BAR VISUALS
        hp_bar, phase_color, phase_label = self.generate_boss_visuals(new_boss_hp, boss["max_hp"])
        player_bar = self.generate_hp_bar(p_hp, p_max_hp, length=8, is_player=True)

        # 5. COMBAT EMBED
        embed = discord.Embed(
            title=f"⚔️ STRIKE: {boss['name']}",
            description=f"**{interaction.user.name}** dealt **{actual_dmg:,}** damage!",
            color=phase_color
        )
        
        embed.add_field(name="👺 Boss Status", value=f"{phase_label}\n{hp_bar}", inline=False)
        embed.add_field(name="👤 Your Vitality", value=player_bar, inline=False)

        if "image" in boss:
            embed.set_thumbnail(url=boss["image"])
            
        BannerManager.apply(embed, type="combat")

        # 6. VICTORY CHECK
        if new_boss_hp <= 0:
            await self.handle_victory(interaction, boss)
        else:
            await interaction.response.send_message(embed=embed)

    def generate_boss_visuals(self, current, max_hp):
        """Internal helper for boss phase styling."""
        percentage = (current / max_hp) * 100
        if percentage > 65:
            return self.generate_hp_bar(current, max_hp), 0x00FF00, "PHASE 1: STABLE"
        elif percentage > 30:
            return self.generate_hp_bar(current, max_hp), 0xFFA500, "PHASE 2: ENRAGED"
        else:
            return self.generate_hp_bar(current, max_hp), 0xFF0000, "PHASE 3: CRITICAL"

    async def handle_victory(self, interaction, boss):
        """Logic for the Top 3 Damage Rewards Table."""
        # Sort tracker: [(user_id, total_dmg), ...]
        sorted_damagers = sorted(self.damage_tracker.items(), key=lambda x: x[1], reverse=True)
        top_3 = sorted_damagers[:3]

        victory_embed = discord.Embed(
            title="🎊 SPECIAL GRADE EXORCISED",
            description=f"The veil lifts as **{boss['name']}** dissipates into cursed energy.",
            color=0x2ecc71
        )

        leaderboard_text = ""
        for i, (u_id, dmg) in enumerate(top_3, 1):
            member = interaction.guild.get_member(int(u_id))
            name = member.name if member else "Unknown Sorcerer"
            
            # Bonus Yen logic (1st: 10k, 2nd: 5k, 3rd: 2.5k)
            bonus = 10000 // (2**(i-1))
            leaderboard_text += f"**#{i} {name}**: `{dmg:,}` dmg (+¥{bonus:,})\n"
            
            # Apply rewards to DB
            await db.players.update_one({"_id": u_id}, {"$inc": {"money": bonus, "xp": 1000}})

        victory_embed.add_field(name="🏆 Top Damage Dealers", value=leaderboard_text or "No data", inline=False)
        BannerManager.apply(victory_embed, type="main")
        
        # Reset tracker for next boss
        self.damage_tracker = {}
        await interaction.response.send_message(embed=victory_embed)

async def setup(bot):
    await bot.add_cog(WorldBossCog(bot))
    
