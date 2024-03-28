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
        self.create_economy_table()
        self.create_protected_users_table()

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

        create_inventory_table_query = """
        CREATE TABLE IF NOT EXISTS inventory (
            user_id INTEGER,
            item TEXT,
            quantidade INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES economy (user_id)
        );
        """
        try:
            c.execute(create_inventory_table_query)
            print("Tabela de inventário criada com sucesso.")
        except sqlite3.Error as e:
            print(e)

    def create_protected_users_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS protected_users (
            user_id INTEGER PRIMARY KEY,
            protected INTEGER DEFAULT 0
        );
        """
        try:
            c = self.conn.cursor()
            c.execute(create_table_query)
            print("Tabela de usuários protegidos criada com sucesso.")
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

    def add_coins(self, user_id, amount):
        try:
            c = self.conn.cursor()
            c.execute("UPDATE economy SET coins = coins + ? WHERE user_id=?", (amount, user_id))
            self.conn.commit()
            print(f"{amount} moedas adicionadas à conta de {user_id}.")
        except sqlite3.Error as e:
            print(e)

    def remove_coins(self, user_id, amount):
        try:
            c = self.conn.cursor()
            c.execute("UPDATE economy SET coins = coins - ? WHERE user_id=?", (amount, user_id))
            self.conn.commit()
            print(f"{amount} moedas removidas da conta de {user_id}.")
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

    @commands.command(name='vender', help='Venda um item por uma quantidade de moedas')
    async def vender(self, ctx, item: str, amount: int):
        if amount <= 0:
            await ctx.send("A quantidade deve ser maior que zero.")
            return

        user_id = ctx.author.id

        # Lógica de venda de itens aqui
        # Por enquanto, vamos assumir que cada item vale 50 moedas
        preco_por_item = 50
        preco_total = preco_por_item * amount

        if not self.user_exists(user_id):
            await ctx.send("Você não possui uma conta. Crie uma com o comando `$saldo`.")
            return

        if amount > 1:
            item = f"{amount} {item}s"

        await ctx.send(f"Você deseja vender {item} por {preco_total} moedas. Confirme com `sim` ou `não`.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['sim', 'não']

        try:
            resposta = await self.bot.wait_for('message', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("Tempo esgotado. A venda foi cancelada.")
            return

        if resposta.content.lower() == 'sim':
            self.add_coins(user_id, preco_total)
            await ctx.send(f"Você vendeu {item} por {preco_total} moedas. Seu saldo atual é de {preco_total} moedas.")
        else:
            await ctx.send("Venda cancelada.")

    @commands.command(name='roubar', help='Rouba uma quantia de moedas de outro usuário')
    async def roubar(self, ctx, member: discord.Member, amount: int):
        if amount <= 0:
            await ctx.send("Você deve especificar uma quantia positiva para roubar.")
            return

        if ctx.author == member:
            await ctx.send("Você não pode roubar de si mesmo.")
            return

        user_id = ctx.author.id
        target_id = member.id

        if not self.user_exists(user_id):
            await ctx.send("Você não possui uma conta. Crie uma com o comando `$saldo`.")
            return

        if not self.user_exists(target_id):
            await ctx.send("O usuário alvo não possui uma conta.")
            return

        if self.is_protected(target_id):
            await ctx.send("O usuário alvo está protegido contra roubo.")
            return

        c = self.conn.cursor()
        c.execute("SELECT coins FROM economy WHERE user_id=?", (target_id,))
        target_coins = c.fetchone()[0]

        if amount > target_coins:
            await ctx.send("O usuário alvo não possui moedas suficientes para roubar essa quantia.")
            return

        if random.randint(1, 100) <= 50:  # 50% de chance de sucesso
            c.execute("UPDATE economy SET coins = coins + ? WHERE user_id=?", (amount, user_id))
            c.execute("UPDATE economy SET coins = coins - ? WHERE user_id=?", (amount, target_id))
            self.conn.commit()
            await ctx.send(f"Você roubou {amount} moedas de {member.display_name}!")
        else:
            await ctx.send("O roubo falhou e você não conseguiu roubar nada.")
            
    def is_protected(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT protected FROM protected_users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        return row is not None and row[0] == 1
        
    @commands.command(name='inventario', help='Mostra seu inventário e itens disponíveis para venda')
    async def inventario(self, ctx):
        user_id = ctx.author.id
        inventario_usuario = self.get_inventory(user_id)
        itens_para_venda = self.get_items_for_sale()

        if not inventario_usuario:
            await ctx.send("Seu inventário está vazio.")
        else:
            inventario_str = "\n".join([f"{item}: {quantidade}" for item, quantidade in inventario_usuario.items()])
            await ctx.send(f"**Seu inventário:**\n{inventario_str}")

        if not itens_para_venda:
            await ctx.send("Não há itens disponíveis para venda no momento.")
        else:
            itens_para_venda_str = "\n".join([f"{item}: {preco} moedas" for item, preco in itens_para_venda.items()])
            await ctx.send(f"**Itens disponíveis para venda:**\n{itens_para_venda_str}")

    def get_inventory(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT item, quantidade FROM inventory WHERE user_id=?", (user_id,))
        rows = c.fetchall()
        inventario = {}
        for row in rows:
            item, quantidade = row
            inventario[item] = quantidade
        return inventario

    def get_items_for_sale(self):
        c = self.conn.cursor()
        c.execute("SELECT item, preco FROM items_for_sale")
        rows = c.fetchall()
        itens_para_venda = {}
        for row in rows:
            item, preco = row
            itens_para_venda[item] = preco
        return itens_para_venda

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

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sorteios_em_andamento = {}  # Dicionário para rastrear os sorteios em andamento
        self.votacoes_em_andamento = {}  # Dicionário para rastrear as votações em andamento

    @commands.command(name='forca', help='Inicia um jogo da forca')
    async def forca(self, ctx):
        palavras = ['python', 'discord', 'bot', 'jogo', 'programacao']  # Lista de palavras para o jogo
        palavra_secreta = random.choice(palavras)
        palavra_atual = ['_'] * len(palavra_secreta)
        letras_erradas = []
        letras_certas = []
        max_tentativas = 6

        embed = discord.Embed(title='Jogo da Forca', description=self.display_forca(palavra_atual, letras_erradas, max_tentativas), color=discord.Color.blue())
        embed.set_footer(text=f'Digite uma letra para adivinhar. Você tem {max_tentativas} tentativas restantes.')
        msg = await ctx.send(embed=embed)

        while True:
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content.isalpha() and len(m.content) == 1

            try:
                resposta = await self.bot.wait_for('message', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send('Tempo esgotado! O jogo da forca foi encerrado.')
                return

            letra = resposta.content.lower()

            if letra in letras_certas or letra in letras_erradas:
                await ctx.send('Você já tentou esta letra. Tente outra.')
                continue

            if letra in palavra_secreta:
                letras_certas.append(letra)
                for i, char in enumerate(palavra_secreta):
                    if char == letra:
                        palavra_atual[i] = char
            else:
                letras_erradas.append(letra)
                max_tentativas -= 1

            embed = discord.Embed(title='Jogo da Forca', description=self.display_forca(palavra_atual, letras_erradas, max_tentativas), color=discord.Color.blue())
            if self.check_vitoria(palavra_atual):
                await msg.edit(embed=embed)
                await ctx.send('Parabéns! Você venceu o jogo da forca!')
                # Adicione a recompensa em dinheiro aqui
                user_id = ctx.author.id
                coins_reward = 200  # Defina o valor de recompensa desejado
                self.bot.get_cog('Economy').add_coins(user_id, coins_reward)
                await ctx.send(f"Parabéns! Você ganhou {coins_reward} moedas.")
                return
            elif max_tentativas == 0:
                embed.set_footer(text='Você excedeu o número máximo de tentativas. O jogo acabou.')
                await msg.edit(embed=embed)
                await ctx.send(f'Que pena! Você perdeu. A palavra era **{palavra_secreta}**.')
                return
            else:
                embed.set_footer(text=f'Digite uma letra para adivinhar. Você tem {max_tentativas} tentativas restantes.')
                await msg.edit(embed=embed)

    def display_forca(self, palavra_atual, letras_erradas, max_tentativas):
        for i in range(len(palavra_atual)):
            if palavra_atual[i] == '_':
                palavra_atual[i] = ':black_large_square:'
        return ' '.join(palavra_atual) + f'\nLetras erradas: {", ".join(letras_erradas)}\nTentativas restantes: {max_tentativas}'

    def check_vitoria(self, palavra_atual):
        return '_' not in palavra_atual

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
bot.add_cog(Games(bot))
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
