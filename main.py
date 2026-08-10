import discord
# Set up message content permissions
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
@client.event
async def on_ready():
    print(f"✅ SUCCESS: {client.user} is online and listening!")
@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return
    # Print incoming messages to Pydroid terminal so you know it's receiving them
    print(f"Received message: {message.content} from {message.author}")
    # Reply to ANY message sent in DMs or when tagged in a server
    if message.guild is None or client.user.mentioned_in(message):
        await message.channel.send("👋 Hey! I received your message!")
# Replace the text below with your actual token
client.run(os.getenv("DISCORD_TOKEN"))
