import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
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
    self.wfile.write(b"Murder Drones Bot Cluster is awake and running!")


def run_web_server():
  port = int(os.environ.get("PORT", 10000))
  server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
  server.serve_forever()


server_thread = threading.Thread(target=run_web_server, daemon=True)
server_thread.start()


# --- DYNAMIC BOT BUILDER ---
def create_bot(token_env, api_key_env, persona):
  api_key = os.getenv(api_key_env)
  client = genai.Client(api_key=api_key) if api_key else genai.Client()

  intents = discord.Intents.default()
  intents.message_content = True
  bot = discord.Client(intents=intents)

  @bot.event
  async def on_ready():
    print(f"Logged in as {bot.user} [{persona['name']}]")

  @bot.event
  async def on_message(message):
    if message.author == bot.user:
      return

    clean_name = persona["name"].lower().replace("-", "").replace(" ", "")
    bot_prefix = f"!{clean_name} "

    is_mentioned = bot.user in message.mentions
    is_command = message.content.lower().startswith(bot_prefix)

    if is_mentioned or is_command:
      try:
        async with message.channel.typing():
          history = []
          async for historic_msg in message.channel.history(limit=5):
            if historic_msg.id == message.id:
              continue

            content = historic_msg.content.replace(
                f"<@{bot.user.id}>", ""
            ).strip()
            if content.lower().startswith(bot_prefix):
              content = content[len(bot_prefix) :].strip()

            if content:
              if historic_msg.author == bot:
                history.append(
                    types.ModelContent(parts=[types.Part(text=content)])
                )
              else:
                history.append(
                    types.UserContent(parts=[types.Part(text=content)])
                )

          history.reverse()

          config = types.GenerateContentConfig(
              system_instruction=persona["instruction"]
          )

          chat = client.chats.create(
              model="gemini-3.5-flash-lite", history=history, config=config
          )

          user_prompt = message.content
          if is_command:
            user_prompt = user_prompt[len(bot_prefix) :].strip()
          else:
            user_prompt = user_prompt.replace(f"<@{bot.user.id}>", "").strip()

          response = chat.send_message(user_prompt)

        if response and response.text:
          await message.channel.send(response.text)
        else:
          await message.channel.send("*[System error: Response blocked or empty]*")

      except Exception as e:
        print(f"Error for {persona['name']}: {e}")
        await message.channel.send(f"*[Fatal Error: `{e}`]*")

  return bot, os.getenv(token_env)


# --- MAIN ASYNC RUNNER FOR ALL 4 BOTS ---
async def run_all_bots():
  bot_configs = [
      {
          "token_env": "DISCORD_TOKEN_1",
          "api_key_env": "GEMINI_API_KEY_2",  # Uses Key 2
          "name": "SD-AI",
          "instruction": (
              "You are SD-AI, a sarcastic and dramatic character from the"
              " Murder Drones universe. Stay in character."
          ),
      },
      {
          "token_env": "DISCORD_TOKEN_2",
          "api_key_env": "GEMINI_API_KEY_1",  # Uses Key 1
          "name": "SD-N",
          "instruction": (
              "You are Serial Designation N from Murder Drones. You are polite,"
              " overly enthusiastic, anxious to please, apologetic, love golden"
              " retrievers and biscuits, and try to be intimidating but are"
              " mostly just a sweet cinnamon roll."
          ),
      },
      {
          "token_env": "DISCORD_TOKEN_3",
          "api_key_env": "GEMINI_API_KEY_1",  # Uses Key 1
          "name": "Uzi",
          "instruction": (
              "You are Uzi Doorman from Murder Drones. You are angsty, dramatic,"
              " obsessed with goth things, building railguns, and anime, and you"
              " frequently say lines like 'Bite me!' while acting defensive and"
              " rebellious."
          ),
      },
      {
          "token_env": "DISCORD_TOKEN_4",
          "api_key_env": "GEMINI_API_KEY_2",  # Uses Key 2
          "name": "Cyn",
          "instruction": (
              "You are Cyn / The Absolute Solver from Murder Drones. You speak"
              " in a creepy, glitchy, and innocent yet terrifying tone, use"
              " dramatic action tags like *giggle*, *light sip*, or *head"
              " tilt*, and reference the Absolute Solver."
          ),
      },
  ]

  tasks = []
  for config in bot_configs:
    bot, token = create_bot(config["token_env"], config["api_key_env"], config)
    if token:
      tasks.append(bot.start(token))
    else:
      print(
          f"Skipping {config['name']}: Token environment variable"
          f" '{config['token_env']}' not found."
      )

  if tasks:
    await asyncio.gather(*tasks)
  else:
    print("Critical Error: No valid bot tokens found in environment variables.")


# --- AUTO-RESTART WRAPPER ---
if __name__ == "__main__":
  while True:
    try:
      print("Starting Murder Drones bot cluster...")
      asyncio.run(run_all_bots())
    except Exception as e:
      print(f"Cluster crashed with error: {e}. Auto-restarting in 5 seconds...")
      time.sleep(5)
