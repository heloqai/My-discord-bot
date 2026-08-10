import os
import discord
import google.generativeai as genai

# Load API keys from your environment variables
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Adjust safety thresholds so fictional sci-fi/drone context doesn't crash the bot
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_ONLY_HIGH",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_ONLY_HIGH",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_ONLY_HIGH",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_ONLY_HIGH",
    },
]

# Initialize the Gemini model with your settings and character persona
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    safety_settings=safety_settings,
    system_instruction=(
        "You are SD-AI, a character from the Murder Drones universe. Stay in"
        " character, be slightly sarcastic or dramatic, and respond accordingly."
    ),
)

# Set up Discord intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
  print(f"Logged in as {client.user} and ready to run!")


@client.event
async def on_message(message):
  # Prevent the bot from replying to itself
  if message.author == client.user:
    return

  # Respond when the bot is mentioned
  if client.user in message.mentions:
    user_prompt = message.content.replace(f"<@{client.user.id}>", "").strip()

    try:
      # Generate response from Gemini API
      response = model.generate_content(user_prompt)

      # Safely verify that response text exists before sending
      if response.text:
        await message.channel.send(response.text)
      else:
        await message.channel.send(
            "*System error: Core temperature spiking... processing blocked by"
            " safety protocols.*"
        )

    except Exception as e:
      # Catch unexpected API errors or safety crashes gracefully
      print(f"Error generating response: {e}")
      await message.channel.send(
          "*Fatal Error: Oil pressure drop detected. Processing halted.*"
      )


# Run the Discord bot using the token stored in your Render environment variables
client.run(os.getenv("DISCORD_TOKEN"))
