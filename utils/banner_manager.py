class BannerManager:
    """
    Centralized visual theme manager for the bot.
    Replace the URLs below with your Canva-designed banners.
    Recommended Size: 1100x440 (Discord Large Image Ratio)
    """
    
    # Standard profile, help, and world info
    MAIN_BANNER = "https://image2url.com/r2/default/images/1771684587824-05c296aa-d67d-4cdc-be90-43b8d6a297b6.png"
    
    # Boss manifestation, raids, and combat results
    COMBAT_BANNER = "https://image2url.com/r2/default/images/1771684587824-05c296aa-d67d-4cdc-be90-43b8d6a297b6.png"
    
    # Configuration, logs, and database updates
    ADMIN_BANNER = "https://image2url.com/r2/default/images/1771684587824-05c296aa-d67d-4cdc-be90-43b8d6a297b6.png"

    @staticmethod
    def apply(embed, type="main"):
        """
        Automatically attaches the requested banner to any Discord Embed.
        
        Args:
            embed (discord.Embed): The embed object to modify.
            type (str): 'main', 'combat', or 'admin'.
            
        Returns:
            discord.Embed: The modified embed with an image set.
        """
        if type == "combat":
            embed.set_image(url=BannerManager.COMBAT_BANNER)
        elif type == "admin":
            embed.set_image(url=BannerManager.ADMIN_BANNER)
        else:
            embed.set_image(url=BannerManager.MAIN_BANNER)
            
        # Optional: You can also set a consistent footer here
        # embed.set_footer(text="Jujutsu Chronicles | Power through Sorcery")
            
        return embed
        
