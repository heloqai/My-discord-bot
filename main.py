import os
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from discord.ext import commands

# --- 1. Fake Web Server (Keeps Render Happy) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is online and healthy!")

    # Quiet the log outputs from the web server
    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# Start web server in a background thread
threading.Thread(target=run_web_server, daemon=True).start()


# --- 2. Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

FUN_RESPONSES = [
    "Hey there! What's on your mind today? 😊",
    "Beep boop! I'm alive and ready to chat! 🤖",
    "Yo! Hope you're having a great day!",
    "Did someone call for a bot? How can I help?",
    "Hey! Tell me a story or ask me a question! ✨"
]

@bot.event
async def on_ready():
    print(f"🎉 SUCCESS! Logged in as: {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Respond if mentioned or in direct messages
    if bot.user.mentioned_in(message) or message.guild is None:
        response = random.choice(FUN_RESPONSES)
        await message.channel.send(response)

    await bot.process_commands(message)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong! 🏓 I'm online!")


# --- 3. Run the Bot ---
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("ERROR: DISCORD_TOKEN is missing from Environment Variables!")
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
