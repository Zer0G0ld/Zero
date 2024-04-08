import discord
import asyncio
import random
import sqlite3

from discord.ext import commands
from commands.utils.data import DataManager

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        self.data_manager = DataManager("data.db")

    @commands.command(name='forca', help='Inicia um jogo da forca')
    async def forca(self, ctx):
        palavras = ['python', 'discord', 'bot', 'jogo', 'programacao']
        palavra_secreta = random.choice(palavras)
        palavra_atual = ['_'] * len(palavra_secreta)
        letras_erradas = []
        max_tentativas = 6

        embed = self.display_forca_embed(palavra_atual, letras_erradas, max_tentativas)
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

            if letra in letras_erradas or letra in palavra_atual:
                await ctx.send('Você já tentou esta letra. Tente outra.')
                continue

            if letra in palavra_secreta:
                palavra_atual = self.update_palavra_atual(palavra_atual, palavra_secreta, letra)
            else:
                letras_erradas.append(letra)
                max_tentativas -= 1

            embed = self.display_forca_embed(palavra_atual, letras_erradas, max_tentativas)

            if self.check_vitoria(palavra_atual):
                await msg.edit(embed=embed)
                await ctx.send('Parabéns! Você venceu o jogo da forca!')
                await self.recompensar_jogador(ctx)
                return
            elif max_tentativas == 0:
                await msg.edit(embed=embed)
                await ctx.send(f'Que pena! Você perdeu. A palavra era **{palavra_secreta}**.')
                return
            else:
                await msg.edit(embed=embed)

    async def recompensar_jogador(self, ctx):
        user_id = ctx.author.id
        coins_reward = 200
        await ctx.send(f"Parabéns! Você ganhou {coins_reward} moedas.")
        await DataManager.add_coins(user_id, coins_reward)

    def update_palavra_atual(self, palavra_atual, palavra_secreta, letra):
        return [letra if char == letra else atual for atual, char in zip(palavra_atual, palavra_secreta)]

    def display_forca_embed(self, palavra_atual, letras_erradas, max_tentativas):
        palavra_display = ' '.join([char if char != '_' else ':black_large_square:' for char in palavra_atual])
        return discord.Embed(
            title='Jogo da Forca',
            description=f'{palavra_display}\nLetras erradas: {", ".join(letras_erradas)}\nTentativas restantes: {max_tentativas}',
            color=discord.Color.blue()
        )

    def check_vitoria(self, palavra_atual):
        return '_' not in palavra_atual
        
    @commands.command(name='velha', help='Inicia um jogo da velha')
    async def jogo_da_velha(self, ctx, opponent: discord.Member):
        if opponent == ctx.author:
            await ctx.send("Você não pode jogar contra você mesmo!")
            return
        if self.get_game(ctx.channel):
            await ctx.send("Já existe um jogo em andamento neste canal.")
            return
        game = JogoVelha(ctx.author, opponent)
        self.games[ctx.channel] = game
        await ctx.send(f"{ctx.author.mention} e {opponent.mention}, o jogo da velha começou! {opponent.mention}, é a sua vez.")
        await ctx.send(game.render_board())

    @commands.command(name='move', help='Faça sua jogada no jogo da velha (use números de 1 a 9 para indicar a posição)')
    async def make_move(self, ctx, position: int):
        game = self.get_game(ctx.channel)
        if not game:
            await ctx.send("Não há jogo em andamento neste canal.")
            return
        if ctx.author != game.current_player:
            await ctx.send("Ainda não é a sua vez de jogar.")
            return
        if not (1 <= position <= 9):
            await ctx.send("Por favor, escolha uma posição válida (de 1 a 9).")
            return
        if not game.make_move(position):
            await ctx.send("Esta posição já está ocupada. Por favor, escolha outra.")
            return
        await ctx.send(game.render_board())
        if game.check_winner() or game.is_board_full():
            winner = game.check_winner()
            if winner:
                await ctx.send(f"Parabéns {winner.mention}, você venceu o jogo da velha!")
            else:
                await ctx.send("O jogo terminou em empate!")
            del self.games[ctx.channel]

    def get_game(self, channel):
        return self.games.get(channel)

class JogoVelha:
    def __init__(self, jogador1, jogador2):
        self.jogador1 = jogador1
        self.jogador2 = jogador2
        self.jogador_atual = jogador1
        self.tabuleiro = [' ' for _ in range(9)]

    def renderizar_tabuleiro(self):
        tabuleiro_str = ""
        for i in range(0, 9, 3):
            tabuleiro_str += " | ".join(self.tabuleiro[i:i+3]) + "\n"
            if i < 6:
                tabuleiro_str += "- " * 5 + "\n"
        return tabuleiro_str

    def comando_ajuda(self, mensagem, argumentos, meta):
        mensagem_ajuda = "= Comandos =\n\n"
    
        for nome_comando, info_comando in meta["comandos"].items():
            if not info_comando.get("apenasDono") or (info_comando.get("apenasDono") and mensagem.author.id == meta["configuracao"]["dono"]):
                if not info_comando.get("apenasAdmin") or (info_comando.get("apenasAdmin") and meta.get("isAdmin")):
                    descricao = info_comando.get("descricao", "Nenhuma descrição fornecida.")
                    mensagem_ajuda += f"{nome_comando.ljust(12)}:: {descricao}\n"

        return f"```asciidoc\n{mensagem_ajuda}```"

    descricao_comando = "Obtenha ajuda sobre um comando."

    meta_comando_ajuda = {
        "executar": comando_ajuda,
        "descricao": descricao_comando
    }


    def make_move(self, position):
        if self.board[position - 1] == ' ':
            self.board[position - 1] = 'X' if self.current_player == self.player1 else 'O'
            self.current_player = self.player2 if self.current_player == self.player1 else self.player1
            return True
        return False

    def check_winner(self):
        lines = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]
        for line in lines:
            if self.board[line[0]] == self.board[line[1]] == self.board[line[2]] != ' ':
                return self.player1 if self.board[line[0]] == 'X' else self.player2
        return None

    def is_board_full(self):
        return ' ' not in self.board
