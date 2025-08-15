import socket
import asyncio
import discord
import os


def port_reachable(host: str, port: int, timeout: int = 8) -> bool:
    """
    Standard Python socket connection check - IPv4 only.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
SERVER = "162.19.28.88"
PORT = 3724
WORLD_SERVER = "135.125.119.89"
WORLD_PORT = 8000
CHECK_INTERVAL = 15  # seconds

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

last_status = None
last_presence_text = None
last_role_status = None

async def update_presence(is_playable):
    global last_presence_text
    text = "✅ Server Online" if is_playable else "🔴 Server Down"

    if text != last_presence_text:
        activity = discord.Game(name=text)
        await client.change_presence(activity=activity, status=discord.Status.online)
        last_presence_text = text

async def update_role(channel, is_playable):
    if channel is None:
        return
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
    # Try to fetch if not cached or CHANNEL_ID wrong type
    if channel is None:
        try:
            channel = await client.fetch_channel(CHANNEL_ID)
        except Exception:
            channel = None
    global last_status

    # Do initial check and setup
    print("Checking authentication server...")
    auth_up = port_reachable(SERVER, PORT, timeout=5)
    print(f"Auth server ({SERVER}:{PORT}): {'UP' if auth_up else 'DOWN'}")
    
    print("Checking world server...")
    world_up = port_reachable(WORLD_SERVER, WORLD_PORT, timeout=5)
    print(f"World server ({WORLD_SERVER}:{WORLD_PORT}): {'UP' if world_up else 'DOWN'}")
    
    # BOTH must be up for server to be playable
    is_playable = auth_up and world_up
    print(f"Server playable: {is_playable}")
    
    # Set initial status
    last_status = is_playable
    await update_presence(is_playable)
    await update_role(channel, is_playable)

    while not client.is_closed():
        auth_up = port_reachable(SERVER, PORT, timeout=5)
        world_up = port_reachable(WORLD_SERVER, WORLD_PORT, timeout=5)

        # BOTH must be up for server to be playable
        is_playable = auth_up and world_up

        # Only update if status changed
        if is_playable != last_status:
            print(f"Status change detected: {'ONLINE' if is_playable else 'DOWN'}")
            print(f"  Auth: {'UP' if auth_up else 'DOWN'}, World: {'UP' if world_up else 'DOWN'}")
            
            if channel is not None:
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