import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager

class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="start", description="Begin your journey as a Sorcerer.")
    async def start(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        exists = await db.players.find_one({"_id": user_id})
        
        if exists:
            return await interaction.response.send_message("❌ You already have a profile!", ephemeral=True)
        
        # Initial Data Structure - Standardized Keys
        new_player = {
            "_id": user_id,
            "name": interaction.user.name,
            "level": 1,
            "xp": 0,
            "money": 500,
            "stat_points": 5,
            "grade": "Grade 4",
            "clan": "None",
            "clan_rerolls": 3,
            "stats": {
                "hp": 500, "current_hp": 500,
                "ce": 100, "cur_ce": 100, # Synchronized pool keys
                "dmg": 20
            },
            "inventory": [],
            "loadout": {
                "technique": None,
                "weapon": None,
                "fighting_style": None
            },
            "mastery": {}
        }
        
        await db.players.insert_one(new_player)
        
        embed = discord.Embed(
            title="⛩️ TOKYO JUJUTSU HIGH",
            description=f"Registration complete. Welcome, **{interaction.user.name}**.\n\nYou have been granted **¥500** and **5 Stat Points** to begin your training.",
            color=0x2b2d31
        )
        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile", description="View your status, loadout, and attributes.")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        data = await db.players.find_one({"_id": str(target.id)})
        
        if not data:
            return await interaction.response.send_message("❌ No profile found. Use `/start` first.", ephemeral=True)
        
        stats = data.get("stats", {})
        loadout = data.get("loadout", {})
        level = data.get("level", 1)
        xp = data.get("xp", 0)
        xp_needed = (level ** 2) * 100
        
        # XP Bar construction
        progress = min(10, int((xp / xp_needed) * 10))
        bar = "▰" * progress + "▱" * (10 - progress)
        
        embed = discord.Embed(title=f"⛩️ SORCERER: {data.get('name', target.name)}", color=0x2b2d31)
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # Status Section
        embed.description = (
            f"**Clan:** `{data.get('clan', 'None')}`\n"
            f"**Grade:** `{data.get('grade', 'Grade 4')}`\n"
            f"**Level:** `{level}`\n"
            f"**XP:** `{bar}` ({xp}/{xp_needed})"
        )
        
        # ACTIVE LOADOUT
        embed.add_field(
            name="🥋 Active Loadout",
            value=f"🌀 **CT:** `{loadout.get('technique', 'None')}`\n"
                  f"⚔️ **Weapon:** `{loadout.get('weapon', 'None')}`\n"
                  f"👊 **Style:** `{loadout.get('fighting_style', 'None')}`",
            inline=False
        )
        
        # STATS - Using Synchronized Keys
        embed.add_field(
            name="📊 Attributes", 
            value=f"❤️ **HP:** `{stats.get('hp')}`\n"
                  f"🧪 **CE:** `{stats.get('ce')}`\n"
                  f"💥 **DMG:** `{stats.get('dmg')}`", 
            inline=True
        )

        embed.add_field(
            name="💰 Assets",
            value=f"💵 **Yen:** ¥{data.get('money', 0):,}\n"
                  f"✨ **SP:** `{data.get('stat_points', 0)}`",
            inline=True
        )

        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="distribute", description="Buff your core attributes.")
    @app_commands.choices(stat=[
        app_commands.Choice(name="Health (HP)", value="hp"),
        app_commands.Choice(name="Cursed Energy (CE)", value="ce"),
        app_commands.Choice(name="Damage (DMG)", value="dmg")
    ])
    async def distribute(self, interaction: discord.Interaction, stat: app_commands.Choice[str], amount: int):
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})
        
        if not player or player.get("stat_points", 0) < amount:
            return await interaction.response.send_message("❌ Insufficient Stat Points.", ephemeral=True)

        if amount <= 0: return await interaction.response.send_message("❌ Enter a valid amount.", ephemeral=True)

        # Mapping and scaling (Using synchronized keys: stats.hp and stats.ce)
        stat_map = {"hp": "stats.hp", "ce": "stats.ce", "dmg": "stats.dmg"}
        pool_map = {"hp": "stats.current_hp", "ce": "stats.cur_ce"}
        
        multiplier = 25 if stat.value in ["hp", "ce"] else 5
        inc_val = amount * multiplier

        update_query = {"$inc": {stat_map[stat.value]: inc_val, "stat_points": -amount}}
        
        # If updating HP or CE, also increase the current pool so they don't have to heal
        if stat.value in pool_map:
            update_query["$inc"][pool_map[stat.value]] = inc_val

        await db.players.update_one({"_id": user_id}, update_query)
        
        await interaction.response.send_message(f"📈 **{stat.name}** increased by **{inc_val}**!")

async def setup(bot):
    await bot.add_cog(PlayerCog(bot))
                      
