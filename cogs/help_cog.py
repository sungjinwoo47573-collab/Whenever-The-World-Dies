import discord
from discord import app_commands
from discord.ext import commands
from database.connection import db

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="View all commands or your current move-set.")
    async def help_cmd(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        player = await db.players.find_one({"_id": user_id})

        embed = discord.Embed(
            title="⛩️ Jujutsu Chronicles: Sorcerer Guide",
            description="Master your cursed energy with the following commands:",
            color=0x2f3136
        )

        # --- COMBAT COMMANDS ---
        combat_info = (
            "👊 **!F1 - !F3** : Use Fighting Style Skills\n"
            "📜 **!CE1 - !CE5** : Use Cursed Technique Skills\n"
            "⚔️ **!W1 - !W4** : Use Weapon Skills\n"
            "🤞 **!Domain** : Expand your Domain (Special Grade only)"
        )
        embed.add_field(name="⚔️ Combat Inputs", value=combat_info, inline=False)

        # --- PLAYER COMMANDS ---
        player_info = (
            "`/profile` : Check Stats & Grade\n"
            "`/inventory` : View owned Techniques/Items\n"
            "`/equip` : Change your current Loadout\n"
            "`/upgrade_stats` : Spend points on HP/CE/DMG"
        )
        embed.add_field(name="👤 Sorcerer Management", value=player_info, inline=False)

        # --- DYNAMIC MOVESET (If Player exists) ---
        if player:
            loadout = player.get("loadout", {})
            tech = loadout.get("technique", "None")
            style = loadout.get("fighting_style", "None")
            weapon = loadout.get("weapon", "None")

            moveset_str = (
                f"🌀 **Tech:** {tech}\n"
                f"👊 **Style:** {style}\n"
                f"🗡️ **Weapon:** {weapon}\n\n"
                "*Equip items to see specific skill names here.*"
            )
            embed.add_field(name="🌀 Your Active Loadout", value=moveset_str, inline=False)

        # --- ADMIN SECTION (Only shows for Admins) ---
        if interaction.user.guild_permissions.administrator:
            admin_info = "`/npc_create`, `/technique_create`, `/raid_create`, `/set_mastery`, `/wipe_everything`"
            embed.add_field(name="🛠️ Admin Suite", value=admin_info, inline=False)

        embed.set_footer(text="The veil protects the weak. The strong protect the veil.")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
      
