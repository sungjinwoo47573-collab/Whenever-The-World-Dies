import discord

class JJKEmbeds:
    @staticmethod
    def profile(data):
        """Standardized UI for /profile showing Stats, XP, Grade, and Money."""
        embed = discord.Embed(title=f"⛩️ Sorcerer Registry: {data['name']}", color=0x2f3136)
        
        # Stats Formatting
        stats = data['stats']
        stats_str = (
            f"❤️ **HP:** {stats['hp']}/{stats['max_hp']}\n"
            f"🧪 **CE:** {stats['ce']}/{stats['max_ce']}\n"
            f"💥 **DMG:** {stats['dmg']}"
        )
        
        # Progress Formatting
        lvl = data['level']
        xp = data['xp']
        xp_needed = lvl * 150
        
        embed.add_field(name="📊 Statistics", value=stats_str, inline=True)
        embed.add_field(name="📜 Status", value=f"**Grade:** {data['grade']}\n**Level:** {lvl}\n**XP:** {xp}/{xp_needed}", inline=True)
        embed.add_field(name="💰 Currency", value=f"**Yen:** ¥{data.get('money', 0):,}", inline=False)
        
        # Equipment/Loadout
        loadout = data.get('loadout', {})
        equip_str = (
            f"🌀 **Tech:** {loadout.get('technique', 'None')}\n"
            f"⚔️ **Weapon:** {loadout.get('weapon', 'None')}\n"
            f"👊 **Style:** {loadout.get('fighting_style', 'None')}"
        )
        embed.add_field(name="🎒 Equipped", value=equip_str, inline=False)
        
        return embed

    @staticmethod
    def combat_log(player_name, target_name, action, damage, is_black_flash=False, effect=None):
        """Visual feedback for !CE, !F, !W inputs."""
        color = 0xff0000 if is_black_flash else 0x7289da
        title = "✨ BLACK FLASH! ✨" if is_black_flash else "⚔️ Combat Action"
        
        embed = discord.Embed(title=title, color=color)
        desc = f"**{player_name}** used **{action}** on **{target_name}**!"
        
        if is_black_flash:
            desc += f"\n# 💥 {damage:,} CRITICAL DMG"
        else:
            desc += f"\n**Damage:** {damage}"
            
        if effect:
            desc += f"\n*{effect}*"
            
        embed.description = desc
        return embed

    @staticmethod
    def raid_announcement(name, boss_name, img_url):
        """UI for /RaidCreate and /NpCspawnchannel."""
        embed = discord.Embed(title=f"🚨 RAID ALERT: {name}", description=f"The veil has dropped. **{boss_name}** has appeared!", color=0x992d22)
        if img_url:
            embed.set_image(url=img_url)
        embed.add_field(name="Join Command", value=f"`/RaidJoin {name}`", inline=False)
        return embed

    @staticmethod
    def success(title, msg):
        return discord.Embed(title=f"✅ {title}", description=msg, color=discord.Color.green())

    @staticmethod
    def error(msg):
        return discord.Embed(title="❌ Error", description=msg, color=discord.Color.red())
        
