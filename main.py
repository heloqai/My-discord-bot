import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from discord.ext import commands
from openai import OpenAI

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


# --- 2. Initialize Grok Client & Discord Bot ---
grok_client = OpenAI(
    api_key=os.getenv("GROK_API_KEY"),
    base_url="https://api.x.ai/v1",
)

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

    # Respond in real time if mentioned or in DMs
    if bot.user.mentioned_in(message) or message.guild is None:
        user_prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        
        if not user_prompt:
            user_prompt = "Hello!"

        try:
            # Using the latest grok-4.5 model
            completion = grok_client.chat.completions.create(
                model="grok-4.5",
                messages=[
                    {"role": "system", "content": "You are a helpful, friendly, and concise Discord bot."},
                    {"role": "user", "content": user_prompt}
                ]
            )
            reply = completion.choices[0].message.content
            await message.channel.send(reply)
        except Exception as e:
            print(f"Grok API Error: {e}")
            await message.channel.send(f"API Error: {e}")

    await bot.process_commands(message)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong! 🏓 I'm online and powered by Grok!")


# --- 3. Run the Bot ---
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("ERROR: DISCORD_TOKEN is missing from Environment Variables!")
