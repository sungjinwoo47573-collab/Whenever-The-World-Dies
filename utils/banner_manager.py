class BannerManager:
    # Replace these with your Canva-designed banners
    MAIN_BANNER = "https://image2url.com/r2/default/images/1771684117733-c25d6ec1-2093-4e70-853e-2846f4906b52.png"
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
      
