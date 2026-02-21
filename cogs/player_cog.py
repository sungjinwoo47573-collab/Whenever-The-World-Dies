import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from database.models import player_model
import random

class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="start", description="Begin your journey as a Sorcerer.")
    async def start(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        exists = await db.players.find_one({"_id": user_id})
        if exists:
            return await interaction.response.send_message("❌ You already have a profile!", ephemeral=True)
        
        # Ensure your player_model includes 'stat_points': 0 by default
        new_player = player_model(user_id, interaction.user.name)
        await db.players.insert_one(new_player)
        await interaction.response.send_message("⛩️ Welcome to Tokyo Jujutsu High. Use `/profile` to see your stats.")

    @app_commands.command(name="profile", description="View your stats, grade, and available points.")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        data = await db.players.find_one({"_id": str(target.id)})
        
        if not data:
            return await interaction.response.send_message("❌ No profile found.", ephemeral=True)
        
        stats = data.get("stats", {})
        stat_points = data.get("stat_points", 0) # Displaying the points
        
        embed = discord.Embed(
            title=f"⛩️ {data['name']}'s Profile",
            description=f"**Clan:** {data.get('clan', 'None')}\n**Grade:** {data.get('grade', 'Grade 4')}",
            color=0x2f3136
        )
        
        embed.add_field(name="📊 Level", value=f"`{data.get('level', 1)}`", inline=True)
        embed.add_field(name="💰 Yen", value=f"`¥{data.get('money', 0):,}`", inline=True)
        embed.add_field(name="✨ Stat Points", value=f"`{stat_points}`", inline=True)
        
        embed.add_field(
            name="⚔️ Combat Attributes", 
            value=(
                f"❤️ **HP:** {stats.get('max_hp', 100)}\n"
                f"🧪 **CE:** {stats.get('max_ce', 100)}\n"
                f"💥 **DMG:** {stats.get('dmg', 10)}"
            ), 
            inline=False
        )

        if target.avatar:
            embed.set_thumbnail(url=target.avatar.url)
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="distribute", description="Spend stat points to buff your character.")
    @app_commands.choices(stat=[
        app_commands.Choice(name="Health (HP)", value="hp"),
        app_commands.Choice(name="Cursed Energy (CE)", value="ce"),
        app_commands.Choice(name="Damage (DMG)", value="dmg")
    ])
    async def distribute(self, interaction: discord.Interaction, stat: app_commands.Choice[str], amount: int):
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})
        
        if amount <= 0:
            return await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)

        current_points = player.get("stat_points", 0)
        if current_points < amount:
            return await interaction.response.send_message(f"❌ Not enough points! You have `{current_points}`.", ephemeral=True)

        # Mapping and Scaling
        stat_map = {"hp": "stats.max_hp", "ce": "stats.max_ce", "dmg": "stats.dmg"}
        # HP/CE get +10 per point, DMG gets +2 per point
        multiplier = 10 if stat.value in ["hp", "ce"] else 2
        inc_val = amount * multiplier

        await db.players.update_one(
            {"_id": user_id},
            {
                "$inc": {
                    stat_map[stat.value]: inc_val, 
                    "stat_points": -amount
                }
            }
        )
        
        await interaction.response.send_message(f"✅ Spent **{amount}** points to increase **{stat.name}** by **{inc_val}**!")

    # ... keep inventory, equip, and use_code from your previous version ...

async def setup(bot):
    await bot.add_cog(PlayerCog(bot))

    
