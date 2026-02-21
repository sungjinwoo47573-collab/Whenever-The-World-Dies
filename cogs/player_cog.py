import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from database.models import player_model
from utils.banner_manager import BannerManager # Ensure this exists!

class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="start", description="Begin your journey as a Sorcerer.")
    async def start(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        exists = await db.players.find_one({"_id": user_id})
        
        if exists:
            return await interaction.response.send_message("❌ You already have a profile!", ephemeral=True)
        
        # Create new player
        new_player = player_model(user_id, interaction.user.name)
        await db.players.insert_one(new_player)
        
        embed = discord.Embed(
            title="⛩️ Welcome to Tokyo Jujutsu High",
            description=f"Welcome, **{interaction.user.name}**. Your journey starts now.\nUse `/profile` to see your stats.",
            color=0x2b2d31
        )
        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile", description="View your stats, grade, and available points.")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        data = await db.players.find_one({"_id": str(target.id)})
        
        if not data:
            return await interaction.response.send_message("❌ No profile found.", ephemeral=True)
        
        stats = data.get("stats", {})
        level = data.get("level", 1)
        xp = data.get("xp", 0)
        xp_needed = (level ** 2) * 100
        
        # XP Bar Construction
        progress = (xp / xp_needed) * 10
        bar = "▰" * int(progress) + "▱" * (10 - int(progress))
        
        embed = discord.Embed(title=f"⛩️ {data['name']}'s Profile", color=0x2b2d31)
        embed.set_thumbnail(url=target.display_avatar.url)
        
        embed.description = (
            f"**Clan:** `{data.get('clan', 'None')}`\n"
            f"**Grade:** `{data.get('grade', 'Grade 4')}`\n"
            f"**Level:** `{level}`\n"
            f"**XP:** `{bar}` ({xp}/{xp_needed})"
        )
        
        embed.add_field(
            name="⚔️ Combat Attributes", 
            value=f"❤️ HP: `{stats.get('max_hp', 100)}` | 🧪 CE: `{stats.get('max_ce', 100)}` | 💥 DMG: `{stats.get('dmg', 10)}`", 
            inline=False
        )

        embed.add_field(
            name="💰 Economy",
            value=f"¥ `{data.get('money', 0):,}` | ✨ Stat Points: `{data.get('stat_points', 0)}`",
            inline=False
        )

        BannerManager.apply(embed, type="main")
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

        stat_map = {"hp": "stats.max_hp", "ce": "stats.max_ce", "dmg": "stats.dmg"}
        multiplier = 10 if stat.value in ["hp", "ce"] else 2
        inc_val = amount * multiplier

        await db.players.update_one(
            {"_id": user_id},
            {"$inc": {stat_map[stat.value]: inc_val, "stat_points": -amount}}
        )
        
        embed = discord.Embed(title="📈 Stats Upgraded", description=f"Increased **{stat.name}** by **{inc_val}**!", color=0x2ecc71)
        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PlayerCog(bot))
                         
