class BannerManager:
    # Replace these with your Canva-designed banners
    MAIN_BANNER = "https://i.imgur.com/your_main_banner.png"
    COMBAT_BANNER = "https://i.imgur.com/your_combat_banner.png"
    ADMIN_BANNER = "https://i.imgur.com/your_admin_banner.png"

    @staticmethod
    def apply(embed, type="main"):
        """Automatically attaches the banner to any embed."""
        if type == "combat":
            embed.set_image(url=BannerManager.COMBAT_BANNER)
        elif type == "admin":
            embed.set_image(url=BannerManager.ADMIN_BANNER)
        else:
            embed.set_image(url=BannerManager.MAIN_BANNER)
        return embed
      
