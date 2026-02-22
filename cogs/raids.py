import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from database.connection import npcs_col, players_col
from config import create_embed, MAIN_COLOR, MAX_RAID_PLAYERS

class Raids(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_raids = {} # {host_id: {"players": [], "boss": data}}

    @app_commands.command(name="raidcreate", description="Define a new Raid setting")
    async def raid_create(self, interaction: discord.Interaction, name: str, boss_name: str, time_limit: int):
        # Admin command to define raid parameters in DB
        await npcs_col.update_one(
            {"name": boss_name}, 
            {"$set": {"raid_name": name, "time_limit": time_limit}}
        )
        await interaction.response.send_message(f"Raid **{name}** featuring **{boss_name}** created.")

    @app_commands.command(name="raidhost", description="Host a lobby for a raid")
    async def raid_host(self, interaction: discord.Interaction, name: str):
        if interaction.user.id in self.active_raids:
            return await interaction.response.send_message("You are already hosting a raid!", ephemeral=True)
        
        self.active_raids[interaction.user.id] = {"name": name, "players": [interaction.user.id]}
        embed = create_embed(
            f"🏰 RAID LOBBY: {name}", 
            f"Host: {interaction.user.mention}\nPlayers: 1/{MAX_RAID_PLAYERS}\n\nUse `/raidjoin` to enter."
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="raidjoin", description="Join an active raid lobby")
    async def raid_join(self, interaction: discord.Interaction, host: discord.Member):
        if host.id not in self.active_raids:
            return await interaction.response.send_message("This lobby does not exist.", ephemeral=True)
        
        lobby = self.active_raids[host.id]
        if len(lobby["players"]) >= MAX_RAID_PLAYERS:
            return await interaction.response.send_message("Raid lobby is full!", ephemeral=True)
        
        if interaction.user.id in lobby["players"]:
            return await interaction.response.send_message("You are already in this lobby.", ephemeral=True)

        lobby["players"].append(interaction.user.id)
        await interaction.response.send_message(f"{interaction.user.mention} joined the raid! ({len(lobby['players'])}/{MAX_RAID_PLAYERS})")

    @app_commands.command(name="raidstart", description="Start the raid and create private instance")
    async def raid_start(self, interaction: discord.Interaction):
        if interaction.user.id not in self.active_raids:
            return await interaction.response.send_message("You are not hosting a raid!", ephemeral=True)
        
        lobby = self.active_raids[interaction.user.id]
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="ACTIVE RAIDS") or await guild.create_category("ACTIVE RAIDS")

        # 1. Create Private Channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        for p_id in lobby["players"]:
            member = guild.get_member(p_id)
            if member: overwrites[member] = discord.PermissionOverwrite(read_messages=True)

        raid_channel = await guild.create_text_channel(name=f"raid-{lobby['name']}", category=category, overwrites=overwrites)

        # 2. Scaling HP Logic (+20% per player)
        player_count = len(lobby["players"])
        base_hp = 10000
        total_hp = base_hp * (1 + (0.20 * player_count))

        embed = create_embed(
            "⚔️ RAID BEGUN", 
            f"The instance has been created: {raid_channel.mention}\nBoss HP scaled to **{int(total_hp)}** due to {player_count} sorcerers."
        )
        await interaction.response.send_message(embed=embed)
        
        await raid_channel.send(f"## RAID START: {lobby['name']}\nExorcise the curse or be removed!")
        # Clean up lobby
        del self.active_raids[interaction.user.id]

async def setup(bot):
    await bot.add_cog(Raids(bot))
      
