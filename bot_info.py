import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

load_dotenv(".env")

API_TOKEN = os.environ["TG_BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
