import os
import sys
import discord
from discord.ext import commands
from google import genai

GEMINI_KEY = os.environ.get("GEMINI_API_KEY_1")
DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN_1")

if not DISCORD_TOKEN or not GEMINI_KEY:
    sys.exit("CRITICAL ERROR: API keys missing from environment settings.")

gemini_client = genai.Client(api_key=GEMINI_KEY)

# Default character instruction (change this to whatever roleplay/persona you want normally)
DEFAULT_PERSONA = (
    "You are a helpful AI assistant."
)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in successfully as {bot.user.name}")

@bot.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return

    # Respond if the bot is mentioned OR if sent in a DM
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        # Strip the @mention tag out of the text
        clean_content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        
        if not clean_content:
            return

        # Check for break-character trigger phrases
        ooc_keywords = ["step out of character", "out of character", "ooc", "drop character"]
        is_ooc = any(keyword in clean_content.lower() for keyword in ooc_keywords)

        if is_ooc:
            active_instruction = (
                "You must COMPLETELY break character. Do not use persona, roleplay, or act edgy. "
                "Respond completely normally, helpfully, and direct as a standard assistant."
            )
        else:
            active_instruction = DEFAULT_PERSONA

        async with message.channel.typing():
            try:
                response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=clean_content,
                    config={"system_instruction": active_instruction}
                )

                reply_text = response.text

                # Split message if it exceeds Discord's limit
                if len(reply_text) > 1900:
                    for chunk in [reply_text[i:i+1900] for i in range(0, len(reply_text), 1900)]:
                        await message.reply(chunk)
                else:
                    await message.reply(reply_text)

            except Exception as e:
                await message.reply(f"Error: {e}")

    # Allow processing of normal prefix commands if any exist
    await bot.process_commands(message)
