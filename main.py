import socket
import asyncio
import discord
import os

import subprocess

import shutil


# --- Linux-only helper to mirror Bash script semantics ---
def port_reachable(host: str, port: int, timeout: int = 3) -> bool:
    pwsh_path = shutil.which("pwsh")
    if pwsh_path:
        try:
            completed = subprocess.run(
                [
                    pwsh_path, "-NoLogo", "-NoProfile", "-Command",
                    f"Test-Connection -TargetName '{host}' -TcpPort {port} "
                    f"-TimeoutSeconds {max(1, int(timeout))} -Quiet"
                ],
                capture_output=True, text=True, timeout=timeout
            )
            if "True" in completed.stdout:
                return True
        except Exception:
            pass
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


# --- minimal helper to mirror PowerShell Test-NetConnection behavior on Windows ---
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

# --- minimal cross platform helper to mirror Bash script ---
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
        auth_up = port_reachable(SERVER, PORT, timeout=5)
        world_up = port_reachable(SERVER, WORLD_PORT, timeout=5)

        is_playable = auth_up and world_up

        if is_playable != last_status:
            guild = channel.guild
            role = discord.utils.get(guild.roles, name="Epoch-Status")

            if role:
                mention = role.mention
                message = f"✅ {mention} - Online" if is_playable else f"🔴 {mention} - Down"
                await channel.send(message, allowed_mentions=discord.AllowedMentions(roles=True))
                last_status = is_playable

        await update_presence(is_playable)
        await update_role(channel, is_playable)

        await asyncio.sleep(CHECK_INTERVAL)

@client.event
async def on_ready():
    print(f"Logged in as {client.user.name}")
    await monitor()

if __name__ == "__main__":
    client.run(TOKEN)
