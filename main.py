
import socket
import asyncio
import discord
from datetime import datetime
import os
import pytz
from threading import Thread
from flask import Flask

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
SERVER = "game.project-epoch.net"
PORT = 3724
WORLD_PORT = 8085
CHECK_INTERVAL = 15  # seconds

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

last_status = None
last_presence_text = None
last_role_status = None

local_tz = pytz.timezone("America/New_York")

app = Flask(__name__)

@app.route("/")
def home():
    return "Epoch bot is running."

def run_flask():
    app.run(host="0.0.0.0", port=8080)

def check_port(host, port):
    try:
        with socket.create_connection((host, port), timeout=5):
            return True
    except:
        return False

async def update_presence(is_playable):
    global last_presence_text
    text = "✅ Server Online" if is_playable else "🔴 Server Down"

    if text != last_presence_text:
        activity = discord.Game(name=text)
        await client.change_presence(activity=activity, status=discord.Status.online)
        last_presence_text = text

async def update_role(channel, is_playable):
    global last_role_status

    guild = channel.guild
    me = guild.get_member(client.user.id)

    desired_role_name = "Online" if is_playable else "Down"
    undesired_role_name = "Down" if is_playable else "Online"

    desired_role = discord.utils.get(guild.roles, name=desired_role_name)
    undesired_role = discord.utils.get(guild.roles, name=undesired_role_name)

    if desired_role and desired_role_name != last_role_status:
        if undesired_role in me.roles:
            await me.remove_roles(undesired_role)
        if desired_role not in me.roles:
            await me.add_roles(desired_role)
        last_role_status = desired_role_name

async def monitor():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    global last_status

    while not client.is_closed():
        now = datetime.now(local_tz).strftime("%Y-%m-%d %I:%M %p %Z")

        auth_up = check_port(SERVER, PORT)
        world_up = check_port(SERVER, WORLD_PORT)

        is_playable = auth_up and world_up

        if is_playable != last_status:
            message = f"[{now}] ✅ Epoch Server - Online" if is_playable else f"[{now}] 🔴 Epoch Server - Down"
            await channel.send(message)
            last_status = is_playable

            await update_presence(is_playable)
            await update_role(channel, is_playable)

        await asyncio.sleep(CHECK_INTERVAL)

@client.event
async def on_ready():
    print(f"Logged in as {client.user.name}")
    await monitor()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    client.run(TOKEN)
