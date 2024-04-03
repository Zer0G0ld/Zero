import discord
import youtube_dl
import asyncio
from discord.ext import commands

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def join_voice_channel(self, ctx):
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.send("Você precisa estar em um canal de voz para usar este comando.")
            return False

        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            ctx.voice_client = await channel.connect()
        return True

    async def get_audio_url(self, url):
        ydl_opts = {'format': 'bestaudio'}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if 'entries' in info:
            return info['entries'][0]['formats'][0]['url']  # Obtém a URL direta do áudio
        else:
            return info['formats'][0]['url']  # Obtém a URL direta do áudio

    async def play_song(self, ctx, url):
        audio_url = await self.get_audio_url(url)
        ctx.voice_client.stop()  # Certifica-se de que não há reprodução anterior
        ctx.voice_client.play(discord.FFmpegPCMAudio(audio_url), after=lambda e: print('done', e))

    @commands.command(name='play', help='Toca música a partir de um URL do YouTube')
    async def play(self, ctx, *, url: str):
        if not await self.join_voice_channel(ctx):
            return

        await self.play_song(ctx, url)

    @commands.command(name='stop', help='Para a música e limpa a fila')
    async def stop(self, ctx):
        voice_client = ctx.voice_client
        if voice_client.is_playing():
            voice_client.stop()
            await ctx.voice_client.disconnect()
