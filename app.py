import os
import discord
import asyncio
import random
import sqlite3

from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv

# Importe as classes das extensões
from commands.Economy import Economy
from commands.Fun import Fun
from commands.Games import Games
from commands.Trapaca import Trapaca
from commands.Moderation import Moderation
from commands.Moderation import Music

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = Intents.default()
intents.messages = True
description = "Um bot para se divertir e administra"

bot = commands.Bot(command_prefix="$", intents=intents, description=description)

def help_command(message, args, meta):
    help_message = "= Comandos =\n\n"
    
    for command_name, command_info in meta["commands"].items():
        if not command_info.get("ownerOnly") or (command_info.get("ownerOnly") and message.author.id == meta["config"]["owner"]):
            if not command_info.get("adminOnly") or (command_info.get("adminOnly") and meta.get("isAdmin")):
                description = command_info.get("description", "Nenhuma descrição fornecida.")
                help_message += f"{command_name.ljust(12)}:: {description}\n"

    return f"```asciidoc\n{help_message}```"

@bot.command(name='link', help='Abre um link fornecido pelo usuário')
async def link(ctx, url: str):
    await ctx.send(f'Aqui está o link que você solicitou: {url}')

@bot.event
async def on_ready():
    print(f"=================================")
    print(f"Estou Online como {bot.user.name}")
    print(f"=================================")

    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                with open('src/saudacao.gif', 'rb') as f:
                    picture = discord.File(f)
                    await channel.send("Olá! Estou online e pronto para interagir.", file=picture)

    conn = bot.get_cog('Economy').create_connection()
    bot.get_cog('Economy').create_economy_table()
    conn.close()


@bot.event
async def on_message(message):
    print(f"Menssagem Recebida: {message.content} ") # Apenas para depuração, fora disso é anti ético

    if not message.author.bot:  # Certifica-se de que o autor da mensagem não seja um bot
        user_id = message.author.id
        if not bot.get_cog('Economy').user_exists(user_id):
            bot.get_cog('Economy').register_new_user(user_id)
            await message.channel.send(f"Bem-vindo, {message.author.mention}! Uma nova conta foi criada para você com 100 moedas iniciais.")
    await bot.process_commands(message)

# Carregar extensões
bot.add_cog(Economy(bot))
bot.add_cog(Fun(bot))
bot.add_cog(Games(bot))
bot.add_cog(Trapaca(bot))
bot.add_cog(Moderation(bot))
bot.add_cog(Music(bot))

bot.run(TOKEN)
