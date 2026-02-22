import discord

class JJKEmbeds:
    @staticmethod
    def profile(data):
        """
        Standardized UI for /profile showing Stats, XP, Grade, and Money.
        Synchronized with current database keys: stats.current_hp and stats.cur_ce.
        """
        embed = discord.Embed(title=f"⛩️ Sorcerer Registry: {data['name']}", color=0x2f3136)
        
        # Stats Formatting (Linked to combat engine keys)
        stats = data.get('stats', {})
        stats_str = (
            f"❤️ **HP:** `{stats.get('current_hp', 0)}` / `{stats.get('max_hp', 0)}`\n"
            f"🧪 **CE:** `{stats.get('cur_ce', 0)}` / `{stats.get('max_ce', 0)}`\n"
            f"💥 **DMG:** `{stats.get('dmg', 0)}`"
        )
        
        # Progress Formatting: (Level^2)*100 scaling
        lvl = data.get('level', 1)
        xp = data.get('xp', 0)
        xp_needed = (lvl ** 2) * 100
        
        embed.add_field(name="📊 Statistics", value=stats_str, inline=True)
        embed.add_field(name="📜 Status", value=f"**Grade:** {data.get('grade', 'Unranked')}\n**Level:** {lvl}\n**XP:** {xp:,}/{xp_needed:,}", inline=True)
        embed.add_field(name="💰 Currency", value=f"**Yen:** ¥{data.get('money', 0):,}", inline=False)
        
        # Equipment/Loadout Mapping
        loadout = data.get('loadout', {})
        equip_str = (
            f"🌀 **Tech:** {loadout.get('technique') or 'None'}\n"
            f"⚔️ **Weapon:** {loadout.get('weapon') or 'None'}\n"
            f"👊 **Style:** {loadout.get('fighting_style') or 'None'}"
        )
        embed.add_field(name="🎒 Equipped", value=equip_str, inline=False)
        
        return embed

    @staticmethod
    def combat_log(player_name, target_name, action, damage, is_black_flash=False, effect=None):
        """Visual feedback for !CE, !F, !W combat inputs."""
        color = 0xff0000 if is_black_flash else 0x7289da
        title = "✨ BLACK FLASH! ✨" if is_black_flash else "⚔️ Combat Action"
        
        embed = discord.Embed(title=title, color=color)
        desc = f"**{player_name}** used **{action}** on **{target_name}**!"
        
        if is_black_flash:
            desc += f"\n# 💥 {damage:,} CRITICAL DMG"
        else:
            desc += f"\n**Damage:** `{damage:,}`"
            
        if effect:
            desc += f"\n\n> {effect}"
            
        embed.description = desc
        return embed

    @staticmethod
    def raid_announcement(name, boss_name, img_url):
        """UI for /RaidCreate and NPC spawn notifications."""
        embed = discord.Embed(
            title=f"🚨 RAID ALERT: {name}", 
            description=f"The veil has dropped. **{boss_name}** has manifested in this sector!", 
            color=0x992d22
        )
        if img_url:
            embed.set_image(url=img_url)
            
        embed.add_field(name="Join Command", value=f"`/raid_join {name}`", inline=False)
        embed.set_footer(text="Prepare your Domain Expansion.")
        return embed

    @staticmethod
    def success(title, msg):
        """Clean success notification for UI consistency."""
        return discord.Embed(title=f"✅ {title}", description=msg, color=discord.Color.green())

    @staticmethod
    def error(msg):
        """Clean error notification for UI consistency."""
        return discord.Embed(title="❌ Error", description=msg, color=discord.Color.red())
            
