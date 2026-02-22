import discord
from datetime import datetime

# --- CORE SETTINGS ---
TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
MONGO_URI = "YOUR_MONGODB_CONNECTION_STRING_HERE"
DATABASE_NAME = "JJK_RPG_DB"

# --- UI & BRANDING ---
MAIN_COLOR = 0x007BFF    # Professional Blue
ADMIN_COLOR = 0xFF4757   # Danger/Admin Red
SUCCESS_COLOR = 0x2ED573 # Success Green

# ASSETS (Replace these with your high-quality hosted images)
BANNER_URL = "https://example.com/jjk_main_banner.png" 
THUMBNAIL_URL = "https://example.com/sorcerer_id_icon.png"
FOOTER_ICON = "https://example.com/jjk_logo_small.png"
FOOTER_TEXT = "Jujutsu Kaisen MMORPG • 2026 Management System"

# --- SYSTEM SETTINGS ---
MAX_RAID_PLAYERS = 12
MAX_WORLD_BOSS_ATTACKERS = 23
BLACK_FLASH_CHANCE = 100 # 1 in 100 chance
XP_PER_MESSAGE = 15      # Base XP for chatting

def create_embed(title: str, description: str, color: int = MAIN_COLOR, user: discord.User = None):
    """
    Standard high-quality embed factory to maintain professional UI
    across all commands.
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now()
    )
    
    if user:
        embed.set_author(name=f"Sorcerer: {user.name}", icon_url=user.display_avatar.url)
    
    embed.set_thumbnail(url=THUMBNAIL_URL)
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=FOOTER_TEXT, icon_url=FOOTER_ICON)
    
    return embed
    
