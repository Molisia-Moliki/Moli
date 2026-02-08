import discord
from discord.ext import commands
import asyncio
import yt_dlp
from dotenv import load_dotenv
import os

# Ładujemy zmienne środowiskowe z .env
load_dotenv()
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    raise ValueError("Brak tokena w zmiennych środowiskowych!")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Kolejka muzyczna: {guild_id: [url1, url2, ...]}
queues = {}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {'format': 'bestaudio'}

# Funkcja odtwarzania kolejki
async def play_queue(ctx, guild_id):
    queue = queues[guild_id]
    while queue:
        url = queue[0]

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['url']
            source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)

        ctx.voice_client.play(source)
        await ctx.send(f"Odtwarzam: **{info['title']}**")

        while ctx.voice_client.is_playing():
            await asyncio.sleep(1)

        queue.pop(0)

    await ctx.voice_client.disconnect()

# /play <URL>
@bot.command()
async def play(ctx, url: str):
    if not ctx.author.voice:
        await ctx.send("Musisz być na kanale głosowym!")
        return

    channel = ctx.author.voice.channel

    if ctx.guild.id not in queues:
        queues[ctx.guild.id] = []

    queues[ctx.guild.id].append(url)
    await ctx.send(f"Dodano do kolejki: {url}")

    if not ctx.voice_client or not ctx.voice_client.is_connected():
        await channel.connect()

    if not ctx.voice_client.is_playing():
        await play_queue(ctx, ctx.guild.id)

# /skip
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Pominięto utwór.")
    else:
        await ctx.send("Nie ma nic do pominięcia.")

# /stop
@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        queues[ctx.guild.id] = []
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("Zatrzymano muzykę i opróżniono kolejkę.")
    else:
        await ctx.send("Nie ma nic do zatrzymania.")

bot.run(TOKEN)
