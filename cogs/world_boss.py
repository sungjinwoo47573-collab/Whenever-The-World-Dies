import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
from database.connection import npcs_col, players_col
from config import create_embed, ADMIN_COLOR

class WorldBoss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_bosses = {} # {channel_id: boss_data}
        self.attackers = {}     # {channel_id: set(user_ids)}

    def get_hp_bar(self, current, max_hp):
        size = 20
        filled = int((current / max_hp) * size)
        return "🟥" * filled + "⬜" * (size - filled)

    @app_commands.command(name="worldbossspawninstant", description="Admin: Spawn a World Boss")
    async def spawn_instant(self, interaction: discord.Interaction, name: str):
        boss_data = await npcs_col.find_one({"name": name})
        if not boss_data:
            return await interaction.response.send_message("Boss not found in database!", ephemeral=True)

        # Initialize Boss Instance
        # Random DMG Buff: 7-16%
        dmg_buff = random.randint(7, 16) / 100
        max_hp = 5000 # Example base HP
        
        self.active_bosses[interaction.channel_id] = {
            "name": name,
            "hp": max_hp,
            "max_hp": max_hp,
            "dmg_buff": dmg_buff,
            "image": boss_data.get("image_url", ""),
            "dialogue": "Know Your Place Fool" # Custom dialogue
        }
        self.attackers[interaction.channel_id] = set()

        embed = create_embed(f"⚠️ WORLD BOSS APPEARED: {name}", f"**Dialogue:** {self.active_bosses[interaction.channel_id]['dialogue']}\n**Buff:** +{int(dmg_buff*100)}% DMG")
        embed.set_image(url=boss_data.get("image_url"))
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id not in self.active_bosses:
            return

        # Check for attack commands (!CT, !F, !W)
        if message.content.startswith(('!CT', '!F', '!W')):
            boss = self.active_bosses[message.channel.id]
            attackers_list = self.attackers[message.channel.id]

            # 23 Player Limit Lock-out
            if message.author.id not in attackers_list:
                if len(attackers_list) >= 23:
                    return await message.reply("The battlefield is full! (Max 23 Sorcerers)")
                attackers_list.add(message.author.id)

            # Simple Damage Logic (Integrating with your Stats)
            player = await players_col.find_one({"user_id": message.author.id})
            dmg = player.get("dmg", 10) if player else 10
            
            boss['hp'] -= dmg
            
            # Show Health Bar after every attack
            hp_bar = self.get_hp_bar(boss['hp'], boss['max_hp'])
            
            if boss['hp'] <= 0:
                await message.channel.send(f"🎊 **{boss['name']} has been EXORCISED!**")
                del self.active_bosses[message.channel.id]
                del self.attackers[message.channel.id]
            else:
                embed = discord.Embed(title=f"💢 {boss['name']} HP", description=f"{hp_bar} ({boss['hp']}/{boss['max_hp']})", color=discord.Color.red())
                await message.channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WorldBoss(bot))
          
