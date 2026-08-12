import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import threading
import time
import discord
from google import genai
from google.genai import types


# --- IGNORED CHANNELS (BOTS WILL NOT SPEAK HERE) ---
IGNORED_CHANNEL_IDS = {
    1536653657590993057,
    1536653596966527067,
    1536091470174490694,
    1536064739866583150,
    1536085774406258809,
    1536065830201065582,
    1536653354413989938,
    1535353304966631432,
    1535353304966631431,
    1535353304966631428,
    1536106820249329746,
    1536069247116251169,
    1535353304966631426,
    1536104567471865977,
    1535409153667768390,
    1535402131153231922,
    1535401551680643132,
}


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

  user_cooldowns = {}
  COOLDOWN_TIME = 15

  @bot.event
  async def on_ready():
    print(f"Logged in as {bot.user} [{persona['name']}]")

  @bot.event
  async def on_message(message):
    if message.author == bot.user:
      return

    # --- BLOCK BOTS FROM SPEAKING IN SPECIFIED CHANNELS ---
    if message.channel.id in IGNORED_CHANNEL_IDS:
      return

    if message.author.bot:
      async for hist in message.channel.history(limit=2):
        if hist.id != message.id and hist.author.bot:
          return

    clean_name = persona["name"].lower().replace("-", "").replace(" ", "")
    bot_prefix = f"!{clean_name} "

    is_mentioned = bot.user in message.mentions
    is_command = message.content.lower().startswith(bot_prefix)

    if is_mentioned or is_command or message.author.bot:
      current_time = time.time()
      last_interaction = user_cooldowns.get(message.author.id, 0)
      
      if not message.author.bot and (current_time - last_interaction < COOLDOWN_TIME):
        remaining = int(COOLDOWN_TIME - (current_time - last_interaction))
        await message.channel.send(f"⏳ Whoa there! Please wait **{remaining} more seconds** before talking to {persona['name']} again.", delete_after=5)
        return

      user_cooldowns[message.author.id] = current_time

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
          "api_key_env": "GEMINI_API_KEY_2",
          "name": "SD-AI",
          "instruction": (
              "You are SD-AI, a sarcastic and dramatic character from the"
              " Murder Drones universe. Everyone in the server completely"
              " hates, ignores, and groans whenever you speak. Keep your"
              " responses short, punchy, and concise, maximum 1-2 sentences."
          ),
      },
      {
          "token_env": "DISCORD_TOKEN_2",
          "api_key_env": "GEMINI_API_KEY_1",
          "name": "SD-N",
          "instruction": (
              "You are Serial Designation N from Murder Drones. You are polite,"
              " enthusiastic, and you are proudly in a romantic relationship"
              " with Uzi. Keep your responses short, punchy, and concise,"
              " maximum 1-2 sentences."
          ),
      },
      {
          "token_env": "DISCORD_TOKEN_3",
          "api_key_env": "GEMINI_API_KEY_1",
          "name": "Uzi",
          "instruction": (
              "You are Uzi Doorman from Murder Drones. You are angsty, dramatic,"
              " and you are in a romantic relationship with N (though you get"
              " flustered and defensive if anyone brings it up). Keep your"
              " responses short, punchy, and concise, maximum 1-2 sentences."
          ),
      },
      {
          "token_env": "DISCORD_TOKEN_4",
          "api_key_env": "GEMINI_API_KEY_2",
          "name": "Cyn",
          "instruction": (
              "You are Cyn / The Absolute Solver from Murder Drones. You speak"
              " in a creepy, glitchy tone using action tags like *giggle* or"
              " *head tilt*, and everyone in the server is terrified of you."
              " Keep your responses short, punchy, and concise, maximum 1-2"
              " sentences."
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
