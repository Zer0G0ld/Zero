import discord
import asyncio
# import random
import logging

from discord.ext import commands
from commands.utils.data import DataManager

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = DataManager("data.db")
        self.data_manager.create_connection()
        self.create_economy_table()
        logging.info("Cog de economia carregada com sucesso.")

    def cog_unload(self):
        # Fecha conexão do banco de dados ao carregar o cog
        self.data_manager.conn.close()
        logging.info("Conexão com o banco de dados encerrada ao descarregar o cog.")

    def create_economy_table(self):
        # Cria as tabelas de economia e registra o bot como usuário, se necessário
        self.data_manager.create_tables()

#        bot_id = self.bot.user.id
#        if not self.data_manager.user_exists(bot_id):
#            self.data_manager.register_new_user(bot_id)
    async def register_bot_user(self):
        bot_id = self.bot.user.id
        if not self.data_manager.user_exists(bot_id):
            self.data_manager.register_new_user(bot_id)
            logging.info(f"Usuário do bot registrado com ID: {bot_id}")

    def add_coins(self, user_id, amount):
        # Usa o método add_coins do DataManager para adicionar moedas ao usuário especificado
        self.data_manager.add_coins(user_id, amount)
        logging.info(f"{amount} moedas adicionadas à conta de {user_id}.")

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"Economy cog está pronta e conectada ao bot.")
        await self.register_bot_user() # Registra o bot quando estiver pronto

    @commands.command(name='saldo', help='Veja seu saldo na sua conta do banco.')
    async def saldo(self, ctx):
        user_id = ctx.author.id
        try:
            coins = self.data_manager.get_user_coins(user_id)
            await ctx.send(f"Seu saldo atual é de {coins} moedas.")
        except UserNotFoundException:
            await ctx.send("Usuário não encontrado.")
        except Exception as e:
            logging.error(f"Erro ao obter saldo: {e}")
            await ctx.send("Ocorreu um erro ao obter o saldo.")


    @commands.command(name='dar', help='Dê um pouco da sua grana para um colega')
    async def dar(self, ctx, member: discord.Member, amount: int):
        if amount <= 0:
            await ctx.send("Você não pode dar uma quantidade negativa de moedas.\nLarga mão de ser mesquinho!")
            return
        if ctx.author == member:
            await ctx.send("Você não pode dar moedas para si mesmo.\nGanancioso demais, credo!")
            return

        user_id = ctx.author.id
        receiver_id = member.id

        try:
            self.data_manager.transfer_coins(user_id, receiver_id, amount)
            await ctx.send(f"{ctx.author.display_name} deu {amount} moedas para {member.display_name}.")
        except InsufficientFundsException:
            await ctx.send("Você não tem moedas suficientes.")
        except UserNotFoundException:
            await ctx.send("Usuário não encontrado.")
        except Exception as e:
            logging.error(f"Error ao transferir moedas: {e}")
            await ctx.send("Ocorreu um erro ao transferir moedas.\nProvavelmente o banco está fechado.\\nTente novamente mais tarde!")

    @commands.command(name='vender', help='Venda um item por uma quantidade de moedas')
    async def vender(self, ctx, item: str, amount: int):
        if amount <= 0:
            await ctx.send("A quantidade deve ser maior que zero.\\nPensa um pouco, como você vende -3?")
            return

        user_id = ctx.author.id
        preco_por_item = 50
        preco_total = preco_por_item * amount

        try:
            await ctx.send(f"Você deseja vender {amount} de {item} por {preco_total} moedas. Confirme com `sim` ou `não`.")
            resposta = await self.bot.wait_for(
                'message', timeout=30.0, check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['sim', 'não']
                )
            if resposta.content.lower() == 'sim':
                self.data_manager.add_coins(user_id, preco_total)
                await ctx.send(f"Você vendeu {amount} de {item} por {preco_total} moedas. Seu saldo atual é de {preco_total} moedas.")
            else:
                await ctx.send("Venda cancelada.")
        except asyncio.TimeoutError:
            await ctx.send("Tempo esgotado. A venda foi cancelada.")
        except Exception as e:
            logging.error(f"Erro ao vender item: {e}")
            await ctx.send("Ocorreu um erro ao vender o item.")

    @commands.command(name='roubar', help='Rouba uma quantia de moedas de outro usuário')
    async def roubar(self, ctx, member: discord.Member, amount: int):
        if amount <= 0:
            await ctx.send("Você deve especificar uma quantia positiva para roubar.\\nAté porque ninguém rouba para ter lucro negativo.")
            return

        if ctx.author == member:
            await ctx.send("Você não pode roubar de si mesmo idiota.")
            return

        user_id = ctx.author.id
        target_id = member.id

        try:
            if not self.data_manager.user_exists(target_id):
                await ctx.send("O usuário alvo não possui uma conta.")
                return

            if self.data_manager.is_protected(target_id):
                await ctx.send("O usuário alvo está protegido contra roubo.")
                return

            if self.data_manager.rob_user(user_id, target_id, amount):
                await ctx.send(f"Você roubou {amount} moedas de {member.display_name}!")
            else:
                await ctx.send("O roubo falhou e você não conseguiu roubar nada.\\nComo não consegue ter sucesso nem em algo simples?")
        except Exception as e:
            logging.error(f"Erro ao roubar moedas: {e}")
            await ctx.send("Ocorreu um erro ao roubar.")

    @commands.command(name='inventario', help='Mostra seu inventário e itens disponíveis para venda')
    async def inventario(self, ctx):
        user_id = ctx.author.id
        try:
            inventario_usuario = self.data_manager.get_inventory(user_id)
            itens_para_venda = self.data_manager.get_items_for_sale()

            inventario_str = "\n".join([f"{item}: {quantidade}" for item, quantidade in inventario_usuario.items()]) if inventario_usuario else "Seu inventário está vazio."
            itens_para_venda_str = "\n".join([f"{item}: {preco} moedas" for item, preco in itens_para_venda.items()]) if itens_para_venda else "Não há itens disponíveis para venda no momento."

            await ctx.send(f"**Seu inventário:**\n{inventario_str}\n\n**Itens disponíveis para venda:**\n{itens_para_venda_str}")
        except Exception as e:
            logging.error(f"Error ao exibir inventário: {e}")
            await ctx.send("Ocorreu um erro ao exibir o inventário e os itens para venda.")

