import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db
from utils.banner_manager import BannerManager

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Guide: View all commands and your active cursed techniques.")
    async def help_cmd(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})

        embed = discord.Embed(
            title="⛩️ JUJUTSU CHRONICLES: SORCERER GUIDE",
            description="Master the art of Cursed Energy. Below are the protocols for engagement.",
            color=0x2b2d31
        )

        # --- COMBAT SYSTEM ---
        combat_info = (
            "🌀 **!CE <1-3>** : Execute Cursed Technique Moves\n"
            "👊 **!F <1-3>** : Execute Fighting Style Strikes\n"
            "⚔️ **!W <1-3>** : Execute Weapon Arts\n"
            "🤞 **!domain** : Attempt Domain Expansion (Requires 100 CE)"
        )
        embed.add_field(name="⚔️ COMBAT PROTOCOLS", value=combat_info, inline=False)

        # --- PROGRESSION SYSTEM ---
        prog_info = (
            "`/profile` : Status, Grade, and Attributes\n"
            "`/inventory` : Owned Techniques & Weapons\n"
            "`/equip` : Assign items to your Loadout\n"
            "`/distribute` : Spend Stat Points on HP/CE/DMG\n"
            "`/stats_reset` : Refund SP (Clan buffs preserved)"
        )
        embed.add_field(name="📜 SORCERER MANAGEMENT", value=prog_info, inline=False)

        # --- DYNAMIC ACTIVE MOVESET ---
        if player:
            loadout = player.get("loadout", {})
            tech_name = loadout.get("technique")
            
            moves_text = ""
            if tech_name:
                # Synchronized with Admin/FightingCog move mapping
                cursor = db.skills.find({"name": tech_name}).sort("move_number", 1)
                moves = await cursor.to_list(length=5)
                if moves:
                    moves_text = "\n".join([f"`!CE {m['move_number']}` : **{m.get('move_title', 'Unknown')}**" for m in moves])
                else:
                    moves_text = f"Equipped: **{tech_name}** (Moves pending sync)"
            else:
                moves_text = "No Cursed Technique equipped."

            embed.add_field(name="🌀 ACTIVE TECHNIQUE MOVES", value=moves_text, inline=False)

        # --- ADMIN SECTION ---
        if interaction.user.guild_permissions.administrator:
            admin_info = "`/wb_create`, `/wb_start`, `/technique_skills`, `/setlevel`, `/addmoney`, `/fix_player_ce`"
            embed.add_field(name="🛠️ HIGHER-UPS (ADMIN)", value=f"||{admin_info}||", inline=False)

        embed.set_footer(text="Through the heavens and earth, I alone am the honored one.")
        BannerManager.apply(embed, type="main")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
    
