class BannerManager:
    # Replace these with your Canva-designed banners
    MAIN_BANNER = "https://image2url.com/r2/default/images/1771684435258-e5e311e9-ce22-42fc-a0ef-93eb78ed4745.png"
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
      
