import discord

def success_embed(title, description):
    embed = discord.Embed(title=f"✅ {title}", description=description, color=0x2ecc71)
    embed.set_footer(text="Jujutsu Chronicles")
    return embed

def error_embed(title, description):
    embed = discord.Embed(title=f"❌ {title}", description=description, color=0xe74c3c)
    return embed
    
