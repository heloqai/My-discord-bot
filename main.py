import os
import discord
from google import genai
from google.genai import types

# Initialize the new Google GenAI client
client = genai.Client()

# Set up Discord intents
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)


@discord_client.event
async def on_ready():
  print(f"Logged in as {discord_client.user} and ready to run!")


@discord_client.event
async def on_message(message):
  # Prevent the bot from replying to itself
  if message.author == discord_client.user:
    return

  # Respond when the bot is mentioned
  if discord_client.user in message.mentions:
    try:
      # Build a short memory window from the last few channel messages
      history = []
      async for historic_msg in message.channel.history(limit=5):
        if historic_msg.id == message.id:
          continue  # Skip the current message itself

        content = historic_msg.content.replace(
            f"<@{discord_client.user.id}>", ""
        ).strip()
        if content:
          if historic_msg.author == discord_client.user:
            history.append(types.ModelContent(parts=[types.Part(text=content)]))
          else:
            history.append(types.UserContent(parts=[types.Part(text=content)]))

      # Ensure chronological order (oldest to newest)
      history.reverse()

      # Define character behavior and system instructions
      config = types.GenerateContentConfig(
          system_instruction=(
              "You are SD-AI, a character from the Murder Drones universe. Stay"
              " in character, be slightly sarcastic or dramatic, and respond"
              " accordingly."
          )
      )

      # Start chat session using the high-quota stable model
      chat = client.chats.create(
          model="gemini-3.5-flash-lite", history=history, config=config
      )

      user_prompt = message.content.replace(
          f"<@{discord_client.user.id}>", ""
      ).strip()
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
discord_client.run(os.getenv("DISCORD_TOKEN"))
