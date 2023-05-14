import asyncio
import time

from asgiref.sync import sync_to_async

from bot import tg_start, send_vacancies_to_bot
from spiders.dou import DouSpider
from spiders.rabota_ua import RabotaUaSpiser
from spiders.work_ua import WorkUaSpider


async def async_spiders():
    await tg_start()
    await DouSpider().start()


def sync_spiders():
    WorkUaSpider().start()
    RabotaUaSpiser().start()


async def main():
    while True:
        await async_spiders()
        await sync_to_async(sync_spiders)()
        await send_vacancies_to_bot()

        time.sleep(100)


if __name__ == '__main__':
    asyncio.run(main())
