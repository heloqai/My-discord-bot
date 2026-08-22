import os
import discord
from discord.ext import commands
from google import genai

# Fetch variables using your specific key names
GEMINI_KEY = os.environ.get("GEMINI_API_KEY_1")
DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN_1")

# Initialize Gemini Client with your specific key variable
gemini_client = genai.Client(api_key=GEMINI_KEY)

# System prompt forcing raw code outputs only
SYSTEM_INSTRUCTION = (
    "You are a raw code generation engine. "
    "Output strictly functional, executable code for the user request. "
    "Do NOT include introductory remarks, markdown headers, conversational explanations, "
    "or closing thoughts. Return ONLY code."
)

# Set up Discord bot intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in successfully as {bot.user.name}")

@bot.command(name="code")
async def generate_code(ctx, *, prompt: str):
    await ctx.send("Generating code...")

    try:
        # Request pure code from Gemini API
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"system_instruction": SYSTEM_INSTRUCTION}
        )

        code_result = response.text

        # Handle Discord's 2000-character message limit safely
        if len(code_result) > 1900:
            for chunk in [code_result[i:i+1900] for i in range(0, len(code_result), 1900)]:
                await ctx.send(f"```\n{chunk}\n```")
        else:
            await ctx.send(f"```\n{code_result}\n```")

    except Exception as e:
        await ctx.send(f"Error generating code: {e}")

bot.run(DISCORD_TOKEN)
