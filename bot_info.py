import os

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Command
from aiogram.utils import executor
from dotenv import load_dotenv

load_dotenv(".env")

API_TOKEN = os.environ["TG_BOT_TOKEN"]
API_HASH = os.environ["API_HASH"]
CHAT_ID = os.environ["CHAT_ID"]

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# vacancy_viewed = "Vacancy viewed"
# cv_sent = "CV sent"
# btn_vacancy_viewed = types.InlineKeyboardButton(text=vacancy_viewed, callback_data="vacancy_viewed")
# btn_cv_sent = types.InlineKeyboardButton(text=cv_sent, callback_data="cv_sent")
# inline_keyboard = types.InlineKeyboardMarkup().add(btn_vacancy_viewed, btn_cv_sent)
#
#
# @dp.message_handler(Command("items"))
# async def test(message: types.Message):
#     await message.answer(
#         text="vacany",
#         reply_markup=inline_keyboard
#     )
#
#
# @dp.message_handler(commands=["vacancy_viewed"])
# async def toggle_view(message: types.Message):
#     await message.answer(text="got it")
#
#
# executor.start_polling(dp)
