import os
import random
import discord
from discord.ext import commands

# 1. Set up Bot Intents
intents = discord.Intents.default()
intents.message_content = True  # Required to read message text

bot = commands.Bot(command_prefix="!", intents=intents)

# 2. Friendly Conversational Responses
FUN_RESPONSES = [
    "Hey there! What's on your mind today? 😊",
    "Beep boop! I'm alive and ready to chat! 🤖",
    "Yo! Hope you're having a great day!",
    "Did someone call for a bot? How can I help?",
    "Hey! Tell me a story or ask me a question! ✨"
]

@bot.event
async def on_ready():
    print(f" SUCCESS! Logged in as: {bot.user.name} ({bot.user.id})")
    print("Bot is online and ready on Render!")

@bot.event
async def on_message(message):
    # Don't let the bot reply to its own messages
    if message.author == bot.user:
        return

    # Check if the message is in a DM or directly mentions/pings the bot
    if bot.user.mentioned_in(message) or message.guild is None:
        response = random.choice(FUN_RESPONSES)
        await message.channel.send(response)

    # Process commands if you add any later (like !ping)
    await bot.process_commands(message)

# 3. Simple Ping Command
@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong! 🏓 I'm online and working!")

# 4. Start the Bot using the Render Environment Variable
token = os.getenv("DISCORD_TOKEN")

if not token:
    print("ERROR: DISCORD_TOKEN environment variable not found on Render!")
else:
    bot.run(token)
