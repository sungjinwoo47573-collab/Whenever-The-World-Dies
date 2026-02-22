import discord
from datetime import datetime
from config import MAIN_COLOR, ADMIN_COLOR, SUCCESS_COLOR, BANNER_URL, THUMBNAIL_URL, FOOTER_TEXT, FOOTER_ICON

class JJKEmbeds:
    @staticmethod
    def base_embed(title: str, description: str, color: int = MAIN_COLOR, user: discord.Member = None):
        """The standard high-quality template used for all commands."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now()
        )
        
        # Author Branding
        if user:
            embed.set_author(name=f"Sorcerer: {user.display_name}", icon_url=user.display_avatar.url)
        else:
            embed.set_author(name="Jujutsu High Management")

        # Visual Identity
        embed.set_thumbnail(url=THUMBNAIL_URL)
        embed.set_image(url=BANNER_URL)
        embed.set_footer(text=FOOTER_TEXT, icon_url=FOOTER_ICON)
        
        return embed

    @staticmethod
    def success(title: str, description: str, user: discord.Member = None):
        """Green-themed success embed."""
        return JJKEmbeds.base_embed(f"✅ {title}", description, color=SUCCESS_COLOR, user=user)

    @staticmethod
    def error(title: str, description: str):
        """Red-themed error embed for admins or failures."""
        return JJKEmbeds.base_embed(f"❌ {title}", description, color=ADMIN_COLOR)

    @staticmethod
    def combat_embed(title: str, description: str, image_url: str = None):
        """Specialized embed for Bosses and Combat with custom images."""
        embed = JJKEmbeds.base_embed(title, description, color=0x000000) # Cursed Black
        if image_url:
            embed.set_image(url=image_url)
        return embed

    @staticmethod
    def leader_embed(title: str, description: str):
        """Gold-themed leaderboard embed."""
        return JJKEmbeds.base_embed(f"🏆 {title}", description, color=0xFFD700)
        
