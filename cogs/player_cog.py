import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from database.models import player_model
from utils.banner_manager import BannerManager

class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="start", description="Begin your journey as a Jujutsu Sorcerer.")
    async def start(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        exists = await db.players.find_one({"_id": user_id})
        
        if exists:
            return await interaction.response.send_message("❌ Your soul is already bound to the school. (Profile exists)", ephemeral=True)
        
        # Initialize new player using your model
        new_player = player_model(user_id, interaction.user.name)
        await db.players.insert_one(new_player)
        
        embed = discord.Embed(
            title="⛩️ WELCOME TO TOKYO JUJUTSU HIGH",
            description=(
                f"Greetings, **{interaction.user.name}**.\n\n"
                "You have been identified as a candidate for the next generation of sorcerers. "
                "Your journey to exorcise curses begins now.\n\n"
                "**Quick Start:**\n"
                "• View your stats with `/profile`.\n"
                "• Train to gain XP with `!train`.\n"
                "• Spend points with `/distribute`."
            ),
            color=0x2b2d31
        )
        
        # Apply the central banner
        BannerManager.apply(embed, type="main")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile", description="View your sorcerer rank, stats, and available points.")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        data = await db.players.find_one({"_id": str(target.id)})
        
        if not data:
            return await interaction.response.send_message("❌ No profile found. Use `/start` to begin.", ephemeral=True)
        
        stats = data.get("stats", {})
        level = data.get("level", 1)
        xp = data.get("xp", 0)
        xp_needed = (level ** 2) * 100
        
        # Progress Bar Logic
        progress = (xp / xp_needed) * 10
        bar = "▰" * int(progress) + "▱" * (10 - int(progress))

        embed = discord.Embed(title=f"⛩️ {data['name']}'s SORCERER FILE", color=0x2b2d31)
        embed.set_thumbnail(url=target.display_avatar.url)
        
        embed.description = (
            f"**Clan:** `{data.get('clan', 'Clanless')}`\n"
            f"**Grade:** `{data.get('grade', 'Grade 4')}`\n"
            f"**Level:** `{level}`\n"
            f"**XP:** `{bar}` ({xp}/{xp_needed})"
        )

        embed.add_field(
            name="⚔️ Combat Prowess", 
            value=f"🩸 HP: `{stats.get('max_hp', 100)}` | 🧪 CE: `{stats.get('max_ce', 100)}` | 💥 DMG: `{stats.get('dmg', 10)}`", 
            inline=False
        )

        embed.add_field(
            name="💰 Assets & Potential",
            value=f"¥ `{data.get('money', 0):,}` | ✨ Points: `{data.get('stat_points', 0)}` | 🧬 Rerolls: `{data.get('clan_rerolls', 0)}`",
            inline=False
        )

        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="inventory", description="View your owned items and techniques.")
    async def inventory(self, interaction: discord.Interaction):
        data = await db.players.find_one({"_id": str(interaction.user.id)})
        if not data: return
        
        techs = data.get("techniques", [])
        items = data.get("inventory", [])
        
        embed = discord.Embed(title="🎒 SORCERER EQUIPMENT", color=0x2b2d31)
        embed.add_field(name="📜 Techniques", value="\n".join([f"• {t}" for t in techs]) if techs else "*None learned*", inline=False)
        embed.add_field(name="🗡️ Weapons/Items", value="\n".join([f"• {i}" for i in items]) if items else "*Empty*", inline=False)
        
        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PlayerCog(bot))
    
