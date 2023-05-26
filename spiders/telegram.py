import asyncio
import datetime

from asgiref.sync import sync_to_async
from telethon.tl import functions

import init_django_module  # noqa F403

import os
from telethon import TelegramClient
from telethon.tl.types import InputPeerChannel, DialogFilter

from spiders.SpiderBlueprint import (
    SendMessageToBotMixin,
    asyncFixFirstVacancyInSessionMixin,
)
from vacancies.models import Telegram, TelegramLastVacancyId


class TelegramSpider(
    SendMessageToBotMixin,
    asyncFixFirstVacancyInSessionMixin
):
    SPIDER_NAME = "telegram"
    SPIDER_MODEL = Telegram

    def __init__(self) -> None:
        self.last_vacancy_id = None
        self.last_vacancy_is_overriden = False
        self.is_first_vacancy_in_session = True

        self.API_ID = int(os.environ["API_ID"])
        self.API_HASH = os.environ["API_HASH"]
        self.client: TelegramClient = TelegramClient(
            "name", self.API_ID, self.API_HASH
        )

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
            for channel in channels:
                channel = await self.client.get_entity(channel)
                today = datetime.datetime.today()
                up_to = today - datetime.timedelta(days=5)  # TODO: in deployment do 20 days

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
                    channel_msg = self.client.iter_messages(channel)

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
                    if not msg_text or not ("python" in msg_text.lower()):
                        continue
                    await sync_to_async(self.SPIDER_MODEL.objects.create)(
                        vacancy_id=msg.id,
                        spider_name=channel_username,
                        publication_date=msg.date,
                        description=msg.message,
                    )

                    await self.fix_first_vacancy_in_session()

        print("TG stop\n")


if __name__ == '__main__':
    asyncio.run(TelegramSpider().start())
