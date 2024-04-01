import discord

from .Music import Music
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name='cls', help='Limpa mensagens do chat')
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, limit: int = 100):
        limit = min(max(1, limit), 1000)
        await ctx.channel.purge(limit=limit+1)  # Limpa mensagens, incluindo o comando
        await ctx.send(f"{limit} mensagens foram excluídas.", delete_after=5)
        
    @commands.command(name='kick', help='Expulsa um membro do servidor')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} foi expulso do servidor.")

    @commands.command(name='ban', help='Bane um membro do servidor')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)
        await ctx.send(f"{member.mention} foi banido do servidor.")

    @commands.command(name='unban', help='Desbane um membro do servidor')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, member: discord.User, *, reason=None):
        await ctx.guild.unban(member, reason=reason)
        await ctx.send(f"{member.mention} foi desbanido do servidor.")

    @commands.command(name='mute', help='Silencia um membro do servidor')
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, reason=None):
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not mute_role:
            await ctx.send("O servidor não possui um cargo de Muted.")
            return
        await member.add_roles(mute_role, reason=reason)
        await ctx.send(f"{member.mention} foi silenciado.")

    @commands.command(name='unmute', help='Remove o silêncio de um membro do servidor')
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member, *, reason=None):
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not mute_role:
            await ctx.send("O servidor não possui um cargo de Muted.")
            return
        await member.remove_roles(mute_role, reason=reason)
        await ctx.send(f"{member.mention} não está mais silenciado.")

    @commands.command(name='warn', help='Avisa um membro do servidor')
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        # Lógica para avisar o membro
        await ctx.send(f"{member.mention} foi avisado por: {reason}")

    @commands.command(name='lock', help='Bloqueia um canal de texto')
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"O canal {channel.mention} foi bloqueado.")

    @commands.command(name='unlock', help='Desbloqueia um canal de texto')
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"O canal {channel.mention} foi desbloqueado.")

def setup(bot):
    bot.add_cog(Moderation(bot))
