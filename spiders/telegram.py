import datetime

from asgiref.sync import sync_to_async
from telethon.tl import functions

import init_django_module  # noqa F403

import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher

from telethon import TelegramClient
from telethon.tl.types import InputPeerChannel, DialogFilter

from vacancies.models import Telegram, TelegramLastVacancyId, FirstVacancySession

load_dotenv(".env")
API_TOKEN = os.environ["TG_BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

client: TelegramClient = TelegramClient("name", API_ID, API_HASH)


async def send_vacancies_to_bot():
    try:
        from_vacancy = await sync_to_async(FirstVacancySession.objects.get)(spider_name="tg")
        if from_vacancy:
            vacancies: list[Telegram] = (await sync_to_async(Telegram.objects.filter)(
                id__gte=from_vacancy.id
            )).order_by("publication_datetime")

            async for vacancy in vacancies:
                await bot.send_message(
                    CHAT_ID,
                    text=f"{vacancy.url_to_vacancy} {vacancy.publication_date} {vacancy.publication_time}",
                    disable_web_page_preview=True
                )
                vacancy.is_sent = True
                await sync_to_async(vacancy.save)()

            await sync_to_async(from_vacancy.delete)()
        await bot.send_message(CHAT_ID, text="—————————————————————", disable_notification=True)
    except FirstVacancySession.DoesNotExist:
        pass


def get_last_vacancy_id(spider_name: str | int) -> int | None:
    try:
        return TelegramLastVacancyId.objects.get(
            spider_name=spider_name
        ).vacancy_id
    except TelegramLastVacancyId.DoesNotExist:
        return None


def save_last_vacancy_id(vacancy_id: int, spider_name: str) -> None:
    try:
        vacancy_meta = TelegramLastVacancyId.objects.get(
            spider_name=spider_name
        )
        vacancy_meta.vacancy_id = vacancy_id
        vacancy_meta.save()

    except TelegramLastVacancyId.DoesNotExist:
        TelegramLastVacancyId.objects.create(
            spider_name=spider_name,
            vacancy_id=vacancy_id
        )


async def tg_start():
    print("TG start")
    async with client:
        folder: DialogFilter = (
            await client(functions.messages.GetDialogFiltersRequest())
        )[1]

        channels: list[InputPeerChannel] = folder.include_peers
        is_first_vacancy_in_session = True
        for channel in channels[:5]:
            channel = await client.get_entity(channel)
            today = datetime.datetime.today()
            up_to = today - datetime.timedelta(days=4)

            try:
                if channel.username:
                    channel_username = channel.username
                else:
                    channel_username = channel.id
            except AttributeError:
                channel_username = channel.id

            last_vacancy = await sync_to_async(get_last_vacancy_id)(channel_username)
            is_overridden_vacancy = False

            if last_vacancy:
                channel_msg = client.iter_messages(channel, min_id=last_vacancy)
            else:
                channel_msg = client.iter_messages(channel)  # next we specify up_to date

            async for msg in channel_msg:
                print(f"t.me/c/{channel_username}/{msg.id}")

                if not last_vacancy:
                    last_vacancy = msg.id
                    await sync_to_async(save_last_vacancy_id)(msg.id, channel_username)
                    is_overridden_vacancy = True

                if not is_overridden_vacancy:
                    await sync_to_async(save_last_vacancy_id)(msg.id, channel_username)
                    is_overridden_vacancy = True

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
                        first_vacancy = await sync_to_async(FirstVacancySession.objects.get)(spider_name="tg")
                        first_vacancy.vacancy_id = vacancy
                        sync_to_async(first_vacancy.save)()
                    except FirstVacancySession.DoesNotExist:
                        await sync_to_async(FirstVacancySession.objects.create)(
                            spider_name="tg",
                            vacancy=vacancy
                        )
    print("TG stop\n")


if __name__ == '__main__':
    asyncio.run(tg_start())
