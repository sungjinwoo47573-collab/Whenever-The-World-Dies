import discord
from discord import app_commands
from discord.ext import commands
from database.connection import techniques_col, players_col
from config import create_embed

class Domains(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="domaincreatefortechnique")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def domain_create(self, interaction: discord.Interaction, name: str, tech: str, hp: int, dmg: int, stm: int, ce: int):
        data = {"name": name, "tech": tech, "hp_b": hp, "dmg_b": dmg, "stm_b": stm, "ce_b": ce}
        await techniques_col.update_one({"domain_name": name}, {"$set": data}, upsert=True)
        await interaction.response.send_message(f"Domain **{name}** linked to **{tech}**.")

    @commands.command(name="domain")
    async def use_domain(self, ctx):
        player = await players_col.find_one({"user_id": ctx.author.id})
        if player.get("domain") == "None":
            return await ctx.send("You have not reached the pinnacle of Jujutsu yet.")
        
        embed = create_embed("🏯 DOMAIN EXPANSION", f"**{ctx.author.display_name}** has opened their domain: **{player['domain']}**!", color=0x000000)
        embed.set_image(url="https://example.com/domain_expansion_gif.gif")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Domains(bot))
  
