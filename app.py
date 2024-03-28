import discord
import asyncio
import random
import sqlite3

from discord import Intents
from discord.ext import commands

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = self.create_connection()

    def create_connection(self):
        try:
            conn = sqlite3.connect("economy.db")
            print("Conexão ao banco de dados estabelecida com sucesso.")
            return conn
        except sqlite3.Error as e:
            print(e)
    
    def create_economy_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS economy (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER DEFAULT 0
        );
        """
        try:
            c = self.conn.cursor()
            c.execute(create_table_query)
            print("Tabela de economia criada com sucesso.")
        except sqlite3.Error as e:
            print(e)

    def user_exists(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM economy WHERE user_id=?", (user_id,))
        row = c.fetchone()
        return row is not None

    def register_new_user(self, user_id):
        try:
            c = self.conn.cursor()
            c.execute("INSERT INTO economy (user_id, coins) VALUES (?, ?)", (user_id, 100))
            self.conn.commit()
            print(f"Novo usuário registrado: {user_id}")
        except sqlite3.Error as e:
            print(e)

    @commands.command(name='saldo', help='Veja seu saldo na sua conta')
    async def saldo(self, ctx):
        user_id = ctx.author.id
        if self.user_exists(user_id):
            c = self.conn.cursor()
            c.execute("SELECT coins FROM economy WHERE user_id=?", (user_id,))
            coins = c.fetchone()[0]
            await ctx.send(f"Seu saldo atual é de {coins} moedas.")
        else:
            await ctx.send("Você ainda não possui uma conta.")

    @commands.command(name='dar', help='Dê um pouco da sua grana para um colega')
    async def dar(self, ctx, member: discord.Member, amount: int):
        if amount < 0:
            await ctx.send("Você não pode dar uma quantidade negativa de moedas.")
            return
        if ctx.author == member:
            await ctx.send("Você não pode dar moedas para si mesmo.")
            return

        user_id = ctx.author.id
        receiver_id = member.id

        if not self.user_exists(user_id):
            await ctx.send("Você não possui uma conta. Crie uma com o comando `$saldo`.")
            return

        c = self.conn.cursor()
        c.execute("UPDATE economy SET coins = coins + ? WHERE user_id=?", (amount, receiver_id))
        c.execute("UPDATE economy SET coins = coins - ? WHERE user_id=?", (amount, user_id))
        self.conn.commit()
        await ctx.send(f"{ctx.author.display_name} deu {amount} moedas para {member.display_name}.")

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
    if ctx.author.id in sorteios_em_andamento:
        await ctx.send("Você já tem um sorteio em andamento!")
        return
        
    await ctx.send(f"Sorteio iniciado! Este sorteio encerrará em {tempo_minutos} minutos. Reaja com 🎉 para participar!")
    sorteios_em_andamento[ctx.author.id] = True
    
    message = await ctx.send("O sorteio começou!")
    await message.add_reaction('🎉')
    
    def check(reaction, user):
        return str(reaction.emoji) == '🎉' and user != bot.user and reaction.message.id == message.id
        
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=tempo_minutos * 60.0, check=check)
    except asyncio.TimeoutError:
        del sorteios_em_andamento[ctx.author.id]
        await ctx.send("Tempo esgotado! Ninguém participou do sorteio. Sorteio cancelado.")
    else:
        del sorteios_em_andamento[ctx.author.id]
        await ctx.send(f"Parabéns, {user.mention}! Você ganhou o sorteio!")

        # Remove a reação do vencedor para evitar que outros cliquem
        await message.clear_reaction('🎉')

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name='cls', help='Limpa mensagens do chat')
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, limit: int = 100):
        limit = min(max(1, limit), 1000)
        await ctx.channel.purge(limit=limit+1)  # Limpa mensagens, incluindo o comando
        await ctx.send(f"{limit} mensagens foram excluídas.", delete_after=5)

TOKEN = "SEU_TOKEN_DISCORD"

intents = Intents.default()
intents.messages = True
description = "Um bot teste"

bot = commands.Bot(command_prefix="$", intents=intents, description=description)
bot.add_cog(Economy(bot))
bot.add_cog(Fun(bot))
bot.add_cog(Moderation(bot))

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

bot.run(TOKEN)

