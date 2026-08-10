import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from discord.ext import commands
from google import genai

# --- 1. Fake Web Server (Keeps Render Happy) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is online and healthy!")

    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()


# --- 2. Initialize Gemini Client & Discord Bot ---
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"SUCCESS! Logged in as: {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Respond when mentioned or in DMs
    if bot.user.mentioned_in(message) or message.guild is None:
        user_prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        
        if not user_prompt:
            user_prompt = "Hello!"

        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=user_prompt,
            )
            reply = response.text
            await message.channel.send(reply)
        except Exception as e:
            print(f"Gemini API Error: {e}")
            await message.channel.send(f"API Error: {e}")

    await bot.process_commands(message)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong! 🏓 I'm online and powered by Gemini!")


# --- 3. Run the Bot ---
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("ERROR: DISCORD_TOKEN is missing from Environment Variables!")
