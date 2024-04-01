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

