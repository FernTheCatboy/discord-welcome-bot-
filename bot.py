#!/usr/bin/env python3
import os
import random
import logging
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
# leave while you still can you dont want to be here i promise you wallahi
TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))

MESSAGES_DIR = Path(__file__).parent / "messages"


def load_welcome_messages(directory: Path) -> list[str]:
    files = sorted(directory.glob("*.txt"))
    messages = [f.read_text(encoding="utf-8").strip() for f in files]
    if not messages:
        raise RuntimeError(f"No .txt message files found in {directory}")
    return messages


WELCOME_MESSAGES = load_welcome_messages(MESSAGES_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("welcome_bot")

intents = discord.Intents.default()
intents.members = True  # required for on_member_join; enable "SERVER MEMBERS INTENT" in the dev portal too

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    logger.info("Logged in as %s (id: %s)", bot.user, bot.user.id)


@bot.event
async def on_member_join(member: discord.Member):
    message = random.choice(WELCOME_MESSAGES)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    try:
        await member.send(message)
        status = f"✅ Sent welcome DM to {member.mention} (`{member}`)."
    except discord.Forbidden:
        status = f"⚠️ Could not DM {member.mention} (`{member}`) — they have DMs disabled."
    except discord.HTTPException as e:
        status = f"❌ Failed to DM {member.mention} (`{member}`): {e}"

    if log_channel:
        await log_channel.send(status)
    else:
        logger.warning("LOG_CHANNEL_ID not set/found; skipping channel log. Status: %s", status)


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN is not set. Copy .env.example to .env and fill in your bot token.")
    bot.run(TOKEN)
