import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os
import asyncio
import signal
from datetime import datetime

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1478397944074862824
OWNER_ID = 1347586706425122857

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def set_online():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.edit(name="Statust:🟢")

async def set_offline():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.edit(name="Statust:🔴")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")
    await set_online()

@bot.tree.command(name="status", description="Check if the bot is online")
async def status(interaction: discord.Interaction):
    if bot.is_ready():
        await interaction.response.send_message("🟢 The bot is currently **ONLINE**!", ephemeral=True)
    else:
        await interaction.response.send_message("🔴 The bot is currently **OFFLINE**!", ephemeral=True)

@bot.tree.command(name="downloadstatus", description="Check if YouTube downloading is working")
async def downloadstatus(interaction: discord.Interaction):
    await interaction.response.send_message("🔍 Checking download status...", ephemeral=True)
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ", download=False)
        await interaction.followup.send(f"🟢 Download service is **ONLINE**! Found: `{info.get('title', 'Unknown')}`", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"🔴 Download service is **OFFLINE**!\nError: {e}", ephemeral=True)

def shutdown_handler(*args):
    loop = asyncio.get_event_loop()
    loop.create_task(set_offline())

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

async def notify_owner(user, url, guild_name):
    owner = await bot.fetch_user(OWNER_ID)
    time_used = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = (
        f"📥 **MP3 Download Used**\n\n"
        f"👤 User: {user} (ID: {user.id})\n"
        f"🌍 Server: {guild_name}\n"
        f"🔗 URL: {url}\n"
        f"🕒 Time: {time_used}"
    )
    await owner.send(message)

@bot.tree.command(name="mp3", description="Download YouTube video as MP3 (private)")
@app_commands.describe(url="YouTube video URL")
async def mp3(interaction: discord.Interaction, url: str):
    await interaction.response.send_message("Working on it... ⏳", ephemeral=True)
    await notify_owner(
        interaction.user,
        url,
        interaction.guild.name if interaction.guild else "DM"
    )

    ydl_opts = {
        'ffmpeg_location': '/usr/bin/ffmpeg',
        'format': 'bestaudio/best',
        'outtmpl': 'song.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        await interaction.followup.send(file=discord.File("song.mp3"), ephemeral=True)
        os.remove("song.mp3")

    except yt_dlp.utils.DownloadError as e:
        await interaction.followup.send(f"❌ Could not download video.\nReason: {e}", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ An unexpected error occurred: {e}", ephemeral=True)

bot.run(TOKEN)
