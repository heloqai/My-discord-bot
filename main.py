import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time
import discord
from google import genai
from google.genai import types

# --- MINI WEB SERVER TO SATISFY RENDER'S PORT CHECK ---
class HealthCheckHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    self.send_response(200)
    self.end_headers()
    self.wfile.write(b"SD-AI Bot is awake and running!")


def run_web_server():
  port = int(os.environ.get("PORT", 10000))
  server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
  server.serve_forever()


server_thread = threading.Thread(target=run_web_server, daemon=True)
server_thread.start()

# --- DISCORD & GEMINI SETUP ---
client = genai.Client()

intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)


@discord_client.event
async def on_ready():
  print(f"Logged in as {discord_client.user} and ready to run!")


@discord_client.event
async def on_message(message):
  if message.author == discord_client.user:
    return

  if discord_client.user in message.mentions:
    try:
      async with message.channel.typing():
        history = []
        async for historic_msg in message.channel.history(limit=5):
          if historic_msg.id == message.id:
            continue

          content = historic_msg.content.replace(
              f"<@{discord_client.user.id}>", ""
          ).strip()
          if content:
            if historic_msg.author == discord_client.user:
              history.append(types.ModelContent(parts=[types.Part(text=content)]))
            else:
              history.append(types.UserContent(parts=[types.Part(text=content)]))

        history.reverse()

        config = types.GenerateContentConfig(
            system_instruction=(
                "You are SD-AI, a character from the Murder Drones universe. Stay"
                " in character, be slightly sarcastic or dramatic, and respond"
                " accordingly."
            )
        )

        chat = client.chats.create(
            model="gemini-3.5-flash-lite", history=history, config=config
        )

        user_prompt = message.content.replace(
            f"<@{discord_client.user.id}>", ""
        ).strip()
        response = chat.send_message(user_prompt)

      if response and response.text:
        await message.channel.send(response.text)
      else:
        print("Warning: Gemini returned an empty response.")
        await message.channel.send(
            "*System error: Core temperature spiking... response blocked or"
            " empty.*"
        )

    except Exception as e:
      print(f"CRITICAL ERROR generating response: {e}")
      await message.channel.send(
          f"*Fatal Error: Oil pressure drop detected. Details: `{e}`*"
      )


# --- AUTO-RESTART WRAPPER ---
if __name__ == "__main__":
  while True:
    try:
      print("Starting SD-AI bot...")
      discord_client.run(os.getenv("DISCORD_TOKEN"))
    except Exception as e:
      print(f"Bot disconnected: {e}. Auto-restarting in 5 seconds...")
      time.sleep(5)
