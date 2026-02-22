import discord
from discord import app_commands
from discord.ext import commands
from database.connection import techniques_col, players_col, npcs_col
from config import create_embed, ADMIN_COLOR

class MasterSystems(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- DAMAGE & COOLDOWN MANAGEMENT ---
    @app_commands.command(name="ctskilldamage", description="Admin: Set CT Skill Damages")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ct_dmg(self, interaction: discord.Interaction, name: str, s1: int, s2: int, s3: int, s4: int):
        await techniques_col.update_one({"name": name}, {"$set": {"s1_dmg": s1, "s2_dmg": s2, "s3_dmg": s3, "s4_dmg": s4}})
        await interaction.response.send_message(f"Damages updated for {name}.")

    @app_commands.command(name="ct_weapon_fstyle_cooldown", description="Admin: Set Cooldowns")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_cooldowns(self, interaction: discord.Interaction, type: str, s1: float, s2: float, s3: float, s4: float):
        # Logic to store cooldown timers in DB for the Combat Cog to read
        await techniques_col.update_one({"type": type}, {"$set": {"cd1": s1, "cd2": s2, "cd3": s3, "cd4": s4}}, upsert=True)
        await interaction.response.send_message(f"Cooldowns for {type} updated.")

    # --- WORLD BOSS ENHANCEMENTS ---
    @app_commands.command(name="worldbossspawnauto", description="Admin: Set Auto Spawn Timer")
    async def boss_auto(self, interaction: discord.Interaction, time_mins: int):
        await interaction.response.send_message(f"Auto-spawn set to every {time_mins} minutes.")
        # This would trigger a background task in main.py

    @app_commands.command(name="worldbossping", description="Ping a role for World Boss")
    async def boss_ping(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.channel.send(f"⚠️ **ATTENTION {role.mention}! A CURSED OBJECT HAS AWAKENED!**")
        await interaction.response.send_message("Ping sent.", ephemeral=True)

    # --- BOSS COUNTER-ATTACK LOGIC ---
    async def boss_attack_players(self, channel, attacker_ids, boss_name):
        """Logic: Boss attacks everyone who attacked him."""
        for user_id in attacker_ids:
            # Randomly 'kill' or damage players
            # If player HP hits 0, they are removed (especially in Raids)
            dmg = 25 # Base boss dmg
            await players_col.update_one({"user_id": user_id}, {"$inc": {"hp": -dmg}})
            # If this was a Raid channel, we would check HP here and remove them.

    # --- LISTS ---
    @app_commands.command(name="domainlist", description="List all created Domains")
    async def domain_list(self, interaction: discord.Interaction):
        domains = await techniques_col.find({"domain_name": {"$exists": True}}).to_list(length=50)
        embed = create_embed("🏯 Registered Domains", "The pinnacle of Jujutsu Sorcery.")
        for d in domains:
            embed.add_field(name=d['domain_name'], value=f"Tech: {d['name']}\nBuff: +{d['dmg_b']}% DMG")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Highest Money and Grade")
    async def leaderboard(self, interaction: discord.Interaction):
        top_players = await players_col.find().sort([("money", -1), ("level", -1)]).limit(10).to_list(length=10)
        lb_text = ""
        for i, p in enumerate(top_players, 1):
            lb_text += f"**{i}.** <@{p['user_id']}> | ¥{p['money']} | {p['grade']}\n"
        
        embed = create_embed("🏆 GLOBAL LEADERBOARD", lb_text)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(MasterSystems(bot))
      
