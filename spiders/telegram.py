import asyncio
import datetime
import time

import aiogram
from aiogram.utils.exceptions import RetryAfter
from asgiref.sync import sync_to_async
from telethon.tl import functions

import init_django_module  # noqa F403

import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher

from telethon import TelegramClient
from telethon.tl.types import InputPeerChannel, DialogFilter

from vacancies.models import Telegram, TelegramLastVacancyId, FirstVacancySession

load_dotenv(".env")

API_TOKEN = os.environ["TG_BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


class TelegramSpider:
    SPIDER_NAME = "telegram"

    def __init__(self):
        self.is_overridden_vacancy = False
        self.last_vacancy_id = False

        self.API_ID = int(os.environ["API_ID"])
        self.API_HASH = os.environ["API_HASH"]
        self.client: TelegramClient = TelegramClient("name", self.API_ID, self.API_HASH)

    @staticmethod
    def get_last_vacancy_id(channel_name: str | int) -> int | None:
        try:
            return TelegramLastVacancyId.objects.get(
                spider_name=channel_name
            ).vacancy_id
        except TelegramLastVacancyId.DoesNotExist:
            return None

    @staticmethod
    def save_last_vacancy_id(vacancy_id: int, channel_name: str | int) -> None:
        try:
            vacancy_meta = TelegramLastVacancyId.objects.get(
                spider_name=channel_name
            )
            vacancy_meta.vacancy_id = vacancy_id
            vacancy_meta.save()

        except TelegramLastVacancyId.DoesNotExist:
            TelegramLastVacancyId.objects.create(
                spider_name=channel_name,
                vacancy_id=vacancy_id
            )

    async def start(self):
        print("TG start")
        async with self.client:
            folder: DialogFilter = (
                await self.client(functions.messages.GetDialogFiltersRequest())
            )[1]

            channels: list[InputPeerChannel] = folder.include_peers
            is_first_vacancy_in_session = True
            for channel in channels[:5]:
                channel = await self.client.get_entity(channel)
                today = datetime.datetime.today()
                up_to = today - datetime.timedelta(days=20)

                try:
                    if channel.username:
                        channel_username = channel.username
                    else:
                        channel_username = channel.id
                except AttributeError:
                    channel_username = channel.id

                self.last_vacancy_id = await sync_to_async(self.get_last_vacancy_id)(channel_username)
                self.is_overridden_vacancy = False

                if self.last_vacancy_id:
                    channel_msg = self.client.iter_messages(channel, min_id=self.last_vacancy_id)
                else:
                    channel_msg = self.client.iter_messages(channel)  # next we specify up_to date

                async for msg in channel_msg:
                    print(f"t.me/c/{channel_username}/{msg.id}")

                    if not self.last_vacancy_id:
                        self.last_vacancy_id = msg.id
                        await sync_to_async(self.save_last_vacancy_id)(msg.id, channel_username)
                        self.is_overridden_vacancy = True

                    if not self.is_overridden_vacancy:
                        await sync_to_async(self.save_last_vacancy_id)(msg.id, channel_username)
                        self.is_overridden_vacancy = True

                    if up_to.date() >= msg.date.date():
                        break

                    msg_text = msg.message
                    if not msg_text or not ("Python" in msg_text or "python" in msg_text):
                        continue

                    await sync_to_async(Telegram.objects.create)(
                        vacancy_id=msg.id,
                        spider_name=channel_username,
                        publication_datetime=msg.date,
                        description=msg.message,
                    )

                    if is_first_vacancy_in_session:
                        is_first_vacancy_in_session = False

                        vacancy = await sync_to_async(Telegram.objects.last)()
                        try:
                            first_vacancy = (
                                await sync_to_async(FirstVacancySession.objects.get)
                                (spider_name=self.SPIDER_NAME)
                            )
                            first_vacancy.vacancy_id = vacancy.id
                            sync_to_async(first_vacancy.save)()
                        except FirstVacancySession.DoesNotExist:
                            await sync_to_async(FirstVacancySession.objects.create)(
                                spider_name=self.SPIDER_NAME,
                                vacancy=vacancy.id
                            )
        print("TG stop\n")

    async def send_vacancies_to_bot(self):
        try:
            from_vacancy = await sync_to_async(FirstVacancySession.objects.get)(spider_name=self.SPIDER_NAME)
            if from_vacancy:
                vacancies: list[Telegram] = (await sync_to_async(Telegram.objects.filter)(
                    id__gte=from_vacancy.id
                )).order_by("publication_datetime")
                n_vacancy = 0
                async for vacancy in vacancies:
                    n_vacancy += 1
                    if n_vacancy == 29:
                        n_vacancy = 0
                        time.sleep(5)
                    await bot.send_message(
                        CHAT_ID,
                        text=f"{vacancy.url_to_vacancy} {vacancy.publication_date} {vacancy.publication_time}",
                        disable_web_page_preview=True
                    )
                    vacancy.is_sent = True
                    await sync_to_async(vacancy.save)()

                await sync_to_async(from_vacancy.delete)()
            await bot.send_message(CHAT_ID, text="—————————————————————", disable_notification=True)
        except FirstVacancySession.DoesNotExist as ex:
            print(ex)


if __name__ == '__main__':
    asyncio.run(TelegramSpider().start())
