import asyncio
import time

from asgiref.sync import sync_to_async

from spiders.dou import DouSpider
from spiders.rabota_ua import RabotaUaSpiser
from spiders.work_ua import WorkUaSpider
from spiders.telegram import TelegramSpider


DELAY_BETWEEN_REQUEST_SESSIONS = 60
# SPIDERS = [WorkUaSpider, RabotaUaSpiser, DouSpider, TelegramSpider]
SPIDERS = [DouSpider]


async def async_spiders():
    # await TelegramSpider().start()
    await DouSpider().start()


def sync_spiders():
    WorkUaSpider().start()
    RabotaUaSpiser().start()


async def send_vacancies_to_bot(spiders: list):
    for spider in spiders:
        await spider().send_vacancies_to_bot()


async def main():
    while True:
        await async_spiders()
        # await sync_to_async(sync_spiders)()
        await send_vacancies_to_bot(SPIDERS)

        time.sleep(DELAY_BETWEEN_REQUEST_SESSIONS)


if __name__ == '__main__':
    asyncio.run(main())
