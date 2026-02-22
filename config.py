import discord

# --- BOT CONFIGURATION ---
TOKEN = "YOUR_DISCORD_TOKEN"
MONGO_URI = "YOUR_MONGODB_URI"
DATABASE_NAME = "JJK_RPG_DB"

# --- UI CONSTANTS ---
# Use a sleek Jujutsu Blue or Cursed Purple
MAIN_COLOR = 0x1a73e8 
ADMIN_COLOR = 0xff4757
SUCCESS_COLOR = 0x2ed573

# EMBED ASSETS (Replace these with your hosted links)
THUMBNAIL_URL = "https://example.com/jjk_logo.png"
BANNER_URL = "https://example.com/jjk_banner.png"
FOOTER_TEXT = "Jujutsu High Management System | 2026"
FOOTER_ICON = "https://example.com/icon.png"

def create_base_embed(title, description, user=None):
    """Helper to maintain high-quality UI across all scripts"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=MAIN_COLOR
    )
    if user:
        embed.set_author(name=user.name, icon_url=user.display_avatar.url)
    embed.set_thumbnail(url=THUMBNAIL_URL)
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=FOOTER_TEXT, icon_url=FOOTER_ICON)
    return embed
  
