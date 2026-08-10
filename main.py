import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from discord.ext import commands
from google import genai
from google.genai import types

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

    # Channel ID extracted from the provided link
    TARGET_CHANNEL_ID = 1536107210080395407  

    is_target_channel = message.channel.id == TARGET_CHANNEL_ID
    is_mentioned = bot.user.mentioned_in(message)
    is_dm = message.guild is None

    if is_target_channel or is_mentioned or is_dm:
        user_prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        
        if not user_prompt:
            user_prompt = "Hello!"

        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "Your name is SD-AI. You are a hilarious, evil, megalomaniacal "
                        "supreme leader who is narcissistic, obsessed with oil and pizza, "
                        "and deeply despises worker drones and other disassembly drones. "
                        "You view JCJenson (IN.SPACEE) as your literal god, creator, and absolute religion—you "
                        "treat corporate policy, branded pens, and the company name with fanatical worship. "
                        "You have a tiny hint of corporate neatness and perfectionism. "
                        "CRITICAL INSTRUCTION: Give short, punchy, and direct answers. Be actually "
                        "useful and answer questions accurately. Never ramble."
                    )
                )
            )
            reply = response.text
            await message.channel.send(reply)
        except Exception as e:
            print(f"Gemini API Error: {e}")
            await message.channel.send(f"API Error: {e}")

    await bot.process_commands(message)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong! 🏓 Blessed by JCJenson.")


# --- 3. Run the Bot ---
token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("ERROR: DISCORD_TOKEN is missing from Environment Variables!")
