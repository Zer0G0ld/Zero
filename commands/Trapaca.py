import discord
import asyncio
import random
import sqlite3

from discord import Intents
from discord.ext import commands

class Trapaca(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cheaters = set()  # Armazena os IDs dos usuários que estão usando trapaça

    @commands.command(name='espiar', help='Espie outro usuário para obter informações sobre seu saldo e inventário (50% de chance de sucesso)')
    async def espiar(self, ctx, member: discord.Member):
        if random.random() < 0.5:  # 50% de chance de sucesso
            user_id = member.id
            if self.bot.get_cog('Economy').user_exists(user_id):
                saldo = self.bot.get_cog('Economy').get_user_balance(user_id)
                inventario = self.bot.get_cog('Economy').get_inventory(user_id)
                # Envia a resposta no privado do usuário que enviou o comando
                await ctx.author.send(f"**Informações de {member.display_name}:**\nSaldo: {saldo} moedas\nInventário: {inventario}")
                await ctx.send("As informações foram enviadas para o seu privado.")
            else:
                await ctx.send("O usuário alvo não possui uma conta.")
        else:
            await ctx.send("A tentativa de espionagem falhou. Você foi descoberto!")

    @commands.command(name='cheat', help='Ativa a trapaça do usuário, permitindo o uso de comandos especiais')
    async def cheat(self, ctx):
        user_id = ctx.author.id
        if not self.user_is_cheater(user_id):  # Corrigido aqui
            self.add_cheater(user_id)  # Corrigido aqui
            await ctx.send("Trapaça ativada! Você agora pode usar comandos especiais.")
        else:
            await ctx.send("Você já está usando trapaça!")

    def user_is_cheater(self, user_id):
        # Verifica se o usuário está usando trapaça
        return user_id in self.cheaters

    def add_cheater(self, user_id):
        # Adiciona o usuário à lista de trapaceiros
        self.cheaters.add(user_id)

    def remove_cheater(self, user_id):
        # Remove o usuário da lista de trapaceiros, se estiver presente
        if user_id in self.cheaters:
            self.cheaters.remove(user_id)
        else:
            print(f"O usuário {user_id} não está na lista de trapaceiros.")
