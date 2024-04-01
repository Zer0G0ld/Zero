import discord
import youtube_dl

from discord.ext import commands

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

    async def join_voice_channel(self, ctx):
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

    @commands.command(name='play', help='Toca música a partir de um URL do YouTube')
    async def play(self, ctx, url: str):
        # Verifica se o bot está em um canal de voz
        if ctx.voice_client is None:
            # Se o bot não estiver em um canal de voz, envie uma mensagem informando o usuário
            await ctx.send("Você precisa estar em um canal de voz para usar este comando.")
            return

        # Tenta extrair informações do vídeo do YouTube
        try:
            # Extrai informações do vídeo do YouTube
            ydl_opts = {'format': 'bestaudio'}
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            # Tenta adicionar a música à fila
            await self.add_to_queue(ctx, info)

        except youtube_dl.utils.DownloadError as e:
            # Se houver um erro ao extrair informações do vídeo do YouTube, envie uma mensagem de erro
            await ctx.send(f"Ocorreu um erro ao tentar reproduzir o vídeo: {e}")
    
    @commands.command(name='pause', help='Pausa a música atual')
    async def pause(self, ctx):
        voice_client = ctx.voice_client
        if voice_client.is_playing():
            voice_client.pause()
            await ctx.send("Música pausada.")
        else:
            await ctx.send("Nenhuma música está sendo reproduzida no momento.")

    @commands.command(name='resume', help='Retoma a música pausada')
    async def resume(self, ctx):
        voice_client = ctx.voice_client
        if voice_client.is_paused():
            voice_client.resume()
            await ctx.send("Música retomada.")
        else:
            await ctx.send("A música não está pausada.")

    @commands.command(name='skip', help='Pula para a próxima música na fila')
    async def skip(self, ctx):
        # Lógica para pular para a próxima música
        pass

    @commands.command(name='queue', help='Mostra a fila de músicas')
    async def queue(self, ctx):
        # Lógica para mostrar a fila de músicas
        pass

    @commands.command(name='stop', help='Para a música e limpa a fila')
    async def stop(self, ctx):
        voice_client = ctx.voice_client
        if voice_client.is_playing():
            voice_client.stop()
            await ctx.send("Música parada.")
        else:
            await ctx.send("Nenhuma música está sendo reproduzida no momento.")
