import discord

class JJKEmbeds:
    """Standardized UI components for the JJK RPG."""

    @staticmethod
    def success(title, description):
        """A clean blue-themed embed for successful actions."""
        return discord.Embed(
            title=f"🌀 {title}",
            description=description,
            color=discord.Color.blue()
        )

    @staticmethod
    def error(description):
        """A red-themed embed for errors or failed requirements."""
        return discord.Embed(
            title="⚠️ Access Denied",
            description=description,
            color=discord.Color.red()
        )

    @staticmethod
    def combat_log(player_name, target_name, action, damage, is_black_flash=False):
        """The UI for every !CE, !F, and !W command."""
        # Black Flash gets a special pitch-black aesthetic
        color = 0x000000 if is_black_flash else 0xFF0000
        title = "✨ BLACK FLASH!" if is_black_flash else "⚔️ Combat Action"
        
        embed = discord.Embed(title=title, color=color)
        embed.add_field(name="Sorcerer", value=player_name, inline=True)
        embed.add_field(name="Target", value=target_name, inline=True)
        embed.add_field(name="Technique", value=f"**{action}**", inline=False)
        
        dmg_val = f"**{damage:,}**"
        if is_black_flash:
            dmg_val = f"💥 `{dmg_val}`"
            
        embed.add_field(name="Result", value=f"{dmg_val} Damage Dealt", inline=True)
        return embed

    @staticmethod
    def profile(data):
        """The /profile UI showing player stats and Grade."""
        embed = discord.Embed(
            title=f"⛩️ Sorcerer Registry: {data['name']}",
            description=f"**Current Rank:** `{data['grade']}`",
            color=0x4B0082 # Dark Purple
        )
        
        stats = data['stats']
        embed.add_field(name="Level", value=f"📊 {data['level']}", inline=True)
        embed.add_field(name="Balance", value=f"¥ {data['money']:,}", inline=True)
        
        hp_bar = f"{stats['hp']}/{stats['max_hp']}"
        ce_bar = f"{stats['ce']}/{stats['max_ce']}"
        
        embed.add_field(name="Status", value=(
            f"❤️ **HP:** `{hp_bar}`\n"
            f"💠 **CE:** `{ce_bar}`\n"
            f"💥 **ATK:** `{stats['dmg']}`"
        ), inline=False)
        
        loadout = data['loadout']
        embed.add_field(name="Current Loadout", value=(
            f"📜 **Tech:** {loadout['technique'] or 'None'}\n"
            f"🥊 **Style:** {loadout['style']}\n"
            f"🗡️ **Weapon:** {loadout['weapon'] or 'None'}"
        ), inline=False)
        
        return embed
      
