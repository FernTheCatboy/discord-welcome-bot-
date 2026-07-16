import logging
import os

import discord
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["DISCORD_BOT_TOKEN"]
SOURCE_CHANNEL_ID = int(os.environ["SOURCE_CHANNEL_ID"])
DEST_CHANNEL_ID = int(os.environ["DEST_CHANNEL_ID"])
REQUIRED_FIELDS = int(os.environ.get("REQUIRED_FIELDS", "5"))
VALID_FORMAT_REPLY = "Logged"
INVALID_FORMAT_REPLY = "Error - Format not followed. Log again or dm @russiancatmaid if you believe this is a mistake"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("log-forwarder")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


def validate_format(content: str, required_fields: int) -> bool:
    """A valid log is exactly `required_fields` non-blank lines, each 'Label: value',
    where value is present and isn't left as a blank/placeholder '*'."""
    lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
    if len(lines) != required_fields:
        return False
    for line in lines:
        if ":" not in line:
            return False
        label, _, value = line.partition(":")
        if not label.strip() or not value.strip() or value.strip() == "*":
            return False
    return True


@client.event
async def on_ready():
    logger.info("Logged in as %s (id=%s)", client.user, client.user.id)
    if client.get_channel(SOURCE_CHANNEL_ID) is None:
        logger.warning("Source channel %s not visible to bot - check ID/permissions", SOURCE_CHANNEL_ID)
    if client.get_channel(DEST_CHANNEL_ID) is None:
        logger.warning("Destination channel %s not visible to bot - check ID/permissions", DEST_CHANNEL_ID)


@client.event
async def on_message(message: discord.Message):
    if message.author.bot or message.channel.id != SOURCE_CHANNEL_ID:
        return

    if validate_format(message.content, REQUIRED_FIELDS):
        dest_channel = client.get_channel(DEST_CHANNEL_ID)
        if dest_channel is None:
            logger.error("Destination channel %s not found; dropping message %s", DEST_CHANNEL_ID, message.id)
            return
        header = f"Logged by **{message.author}** — {message.jump_url}"
        try:
            await dest_channel.send(f"{header}\n{message.content}")
        except discord.HTTPException:
            logger.exception("Failed to forward message %s", message.id)
            return
        try:
            await message.reply(VALID_FORMAT_REPLY)
        except discord.HTTPException:
            logger.exception("Failed to reply to message %s", message.id)
    else:
        try:
            await message.reply(INVALID_FORMAT_REPLY)
        except discord.HTTPException:
            logger.exception("Failed to reply to message %s", message.id)


if __name__ == "__main__":
    client.run(TOKEN, log_handler=None)

