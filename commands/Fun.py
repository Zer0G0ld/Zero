import discord
import asyncio
import random
import sqlite3

from discord import Intents
from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sorteios_em_andamento = {}  # Dicionário para rastrear os sorteios em andamento
        self.votacoes_em_andamento = {}  # Dicionário para rastrear as votações em andamento

    @commands.command(name='obg', help='Agradeça ao bot')
    async def obg(self, ctx):
        respostas = ["nd", "Nada", "tmj", "Tá suave", "Rlx", "É nois", "Só fiz meu trabalho!"]
        await ctx.send(random.choice(respostas))

    @commands.command(name='oi', help='Tente dizer oi')
    async def oi(self, ctx):
        respostas = ["Olá!", "Oi, tudo bem?", "E ai? como vai?", "Oi!", "Olá! como vai meu mestre?", "Olá mestre!", "Bem-vindo de volta mestre"]
        await ctx.send(random.choice(respostas))
        
        
    @commands.command(name='trivia', help='Inicia um jogo de trivia')
    async def trivia(self, ctx):
        perguntas_trivia = {
            "Qual é a capital da França?": "Paris",
            "Quem escreveu 'Romeu e Julieta'?": "William Shakespeare",
            "Quantos continentes existem na Terra?": "Sete",
            "Qual a soma de todos os ângulos internos?": "180°",
        }
        
        pergunta, resposta = random.choice(list(perguntas_trivia.items()))
        await ctx.send(f"Bem-vindo ao jogo de Trivia! {pergunta}")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            answer = await self.bot.wait_for('message', timeout=20.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"Tempo esgotado! A resposta correta era: {resposta}")
        else:
            if answer.content.strip().lower() == resposta.lower():
                await ctx.send("Correto!")
                # Adicione moedas ao jogador
                user_id = ctx.author.id
                coins_reward = 100  # Defina o valor de recompensa desejado
                self.bot.get_cog('Economy').add_coins(user_id, coins_reward)
                await ctx.send(f"Parabéns! Você ganhou {coins_reward} moedas.")
            else:
                await ctx.send(f"Incorreto! A resposta correta era: {resposta}")

    @commands.command(name='votacao', help='Inicia uma votação com as escolhas fornecidas e o tempo especificado')
    async def votacao(self, ctx, tempo_minuto: int = 1, *choices: str):
        if ctx.author.id in self.votacoes_em_andamento:
            await ctx.send("Você já tem uma votação em andamento!")
            return
    
        if len(choices) < 2:
            await ctx.send("Você precisa fornecer pelo menos duas opções para a votação.")
            return
        
        try:
            tempo_minutos = int(tempo_minuto)
            if tempo_minutos <= 0:
                raise ValueError
        except ValueError:
            await ctx.send("O tempo deve ser um número inteiro positivo. Usando o valor padrão de 1 minuto.")
            tempo_minutos = 1
    
        await ctx.send(f"Votação iniciada! Esta votação encerrará em {tempo_minutos} minutos.")
        self.votacoes_em_andamento[ctx.author.id] = choices
    
        formatted_choices = "\n".join([f"{index + 1}. {choice}" for index, choice in enumerate(choices)])
        message = await ctx.send(f"Escolha uma opção digitando o número correspondente: \n{formatted_choices}")
    
        for i in range(1, len(choices) + 1):
            await message.add_reaction(f"{i}\u20e3")  # Adiciona reação com emoji numérico

        await asyncio.sleep(tempo_minutos * 60)  # Aguarda o tempo especificado em minutos

        del self.votacoes_em_andamento[ctx.author.id]
        await ctx.send("A votação encerrou!")
        # Contagem dos votos
        reactions = message.reactions
        vote_count = {index: reaction.count - 1 for index, reaction in enumerate(reactions) if reaction.count > 1}

        if not vote_count:
            await ctx.send("Nenhum voto foi registrado.")
            return

        max_votes = max(vote_count.values())
        winners = [index + 1 for index, votes in vote_count.items() if votes == max_votes]

        if len(winners) == 1:
            await ctx.send(f"A opção vencedora com {max_votes} voto(s) é a opção {winners[0]}: {choices[winners[0] - 1]}")
        else:
            await ctx.send(f"Houve um empate entre as opções: {' '.join([f'opção {winner}: {choices[winner - 1]}' for winner in winners])}")

    @commands.command(name='sorteio', help='Inicia um sorteio com o tempo especificado')
    async def sorteio(self, ctx, tempo_minutos: int = 1):
        if ctx.author.id in self.sorteios_em_andamento:
            await ctx.send("Você já tem um sorteio em andamento!")
            return
        
        await ctx.send(f"Sorteio iniciado! Este sorteio encerrará em {tempo_minutos} minutos. Reaja com 🎉 para participar!")
        self.sorteios_em_andamento[ctx.author.id] = True
        
        message = await ctx.send("O sorteio começou!")
        await message.add_reaction('🎉')
        
        def check(reaction, user):
            return str(reaction.emoji) == '🎉' and user != bot.user and reaction.message.id == message.id
            
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=tempo_minutos * 60.0, check=check)
        except asyncio.TimeoutError:
            del self.sorteios_em_andamento[ctx.author.id]
            await ctx.send("Tempo esgotado! Ninguém participou do sorteio. Sorteio cancelado.")
        else:
            del self.sorteios_em_andamento[ctx.author.id]
            await ctx.send(f"Parabéns, {user.mention}! Você ganhou o sorteio!")

            # Remove a reação do vencedor para evitar que outros cliquem
            await message.clear_reaction('🎉')
