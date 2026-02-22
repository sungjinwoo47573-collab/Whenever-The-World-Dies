import discord

class BannerManager:
    """
    Standardizes the look of all bot embeds.
    Usage: BannerManager.apply(embed, type="main")
    """
    COLORS = {
        "main": 0x2b2d31,     # Dark Gray (Standard)
        "admin": 0x00fbff,    # Cyan (Admin Actions)
        "combat": 0xe74c3c,   # Red (Battle/Bosses)
        "success": 0x2ecc71,  # Green (Gains/Rerolls)
        "domain": 0x000000    # Black (Domain Expansion)
    }

    @staticmethod
    def apply(embed: discord.Embed, type: str = "main"):
        # Apply theme color
        embed.color = BannerManager.COLORS.get(type, BannerManager.COLORS["main"])
        
        # Set standardized footer with bot branding
        embed.set_footer(text="⛩️ Jujutsu Chronicles | Domain: Active")
        
        # Optional: Set a consistent thumbnail if desired
        embed.set_thumbnail(url="https://image2url.com/r2/default/images/1771684587824-05c296aa-d67d-4cdc-be90-43b8d6a297b6.png")
        
        return embed
        
