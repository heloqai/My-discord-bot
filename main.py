import os
import discord
import google.generativeai as genai

# Load API keys from your environment variables
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Safety thresholds to prevent fictional sci-fi context crashes
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

# Initialize the Gemini model
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
    try:
      # Build a short memory window from the last few channel messages (e.g., last 4)
      history = []
      async for historic_msg in message.channel.history(limit=5):
        if historic_msg.id == message.id:
          continue  # Skip the current message itself

        # Determine if the message came from the bot or a user
        role = "model" if historic_msg.author == client.user else "user"

        # Clean bot mentions out of the text history
        content = historic_msg.content.replace(f"<@{client.user.id}>", "").strip()
        if content:
          # Insert at the beginning to keep chronological order (oldest to newest)
          history.insert(0, {"role": role, "parts": [content]})

      # Start a chat session with this restricted history
      chat = model.start_chat(history=history)

      # Get the clean prompt text for the current message
      user_prompt = message.content.replace(f"<@{client.user.id}>", "").strip()

      # Send the message within the short chat session context
      response = chat.send_message(user_prompt)

      if response.text:
        await message.channel.send(response.text)
      else:
        await message.channel.send(
            "*System error: Core temperature spiking... processing blocked by"
            " safety protocols.*"
        )

    except Exception as e:
      print(f"Error generating response: {e}")
      await message.channel.send(
          "*Fatal Error: Oil pressure drop detected. Processing halted.*"
      )


# Run the Discord bot using your Render token
client.run(os.getenv("DISCORD_TOKEN"))
