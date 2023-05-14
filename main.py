import asyncio
import time

from asgiref.sync import sync_to_async

from spiders.dou import DouSpider
from spiders.rabota_ua import RabotaUaSpiser
from spiders.work_ua import WorkUaSpider
from spiders.telegram import tg_start, send_vacancies_to_bot


DELAY_BETWEEN_REQUEST_SESSIONS = 60


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

        time.sleep(DELAY_BETWEEN_REQUEST_SESSIONS)


if __name__ == '__main__':
    asyncio.run(main())
