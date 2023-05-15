import asyncio
import time

import requests as requests
from asgiref.sync import sync_to_async
from playwright.async_api import ElementHandle, async_playwright

import init_django_module  # noqa F403


from bs4 import BeautifulSoup


from spiders.SpiderBlueprint import AsyncSpiderBlueprint
from spiders.telegram import bot, CHAT_ID
from vacancies.models import FirstVacancySession, Dou


class DouSpider(AsyncSpiderBlueprint):
    SPIDER_NAME = "dou"
    URL = "https://jobs.dou.ua/vacancies/?search=python+-senior+-lead"
    DATE_FORMAT = "%d %B %Y"
    is_first_vacancy_in_session = True

    @staticmethod
    async def btn_more_click(page) -> bool | None:
        btn_more = page.locator(".more-btn a")
        btn_is_hidden = await btn_more.get_attribute("style")
        if btn_is_hidden:
            return None
        return btn_more

    @staticmethod
    async def get_value_or_none(element: ElementHandle):
        if element:
            return (await element.text_content()).strip()
        return None

    async def get_vacancy_info(self, vacancy):
        vacancy_id = int(await vacancy.get_attribute("_id"))
        title = await self.get_value_or_none(await vacancy.query_selector(".title .vt"))
        company_name = await self.get_value_or_none(await vacancy.query_selector(".company"))
        location_work = await self.get_value_or_none(await vacancy.query_selector(".cities"))
        publication_date = await self.get_value_or_none(await vacancy.query_selector(".date"))
        url_to_vacancy = await (await vacancy.query_selector(".vt")).get_attribute("href")
        if publication_date:
            publication_date = await self.str_to_date(publication_date)
        salary_block = await self.get_value_or_none(await vacancy.query_selector(".salary"))

        salary_from = None
        salary_to = None
        salary = None
        if salary_block:
            sal = salary_block
            if "–" in sal:
                sal = sal.replace("$", "")
                salary_from, salary_to = [int(n) for n in sal.split("–")]
            elif "до" in sal:
                salary_to = int(sal.split("$")[1])
            elif "від":
                salary_from = int(sal.split("$")[1])

        return {
            "vacancy_id": vacancy_id,
            "title": title,
            "company_name": company_name,
            "location_work": location_work,
            "salary_from": salary_from,
            "salary_to": salary_to,
            "salary": salary,
            "publication_date": publication_date,
            "url_to_vacancy": url_to_vacancy,
        }

    async def parse_vacancies(self, page) -> None:
        await page.goto(self.URL)
        is_stop = False
        n_vac = 0
        self.last_vacancy_id = await sync_to_async(self.get_last_vacancy_id)()
        while True:
            await page.wait_for_selector(".vacancy")
            vacancies = await page.query_selector_all(".vacancy")
            vacancies = vacancies[n_vac::]
            for vacancy in vacancies:
                n_vac += 1

                vacancy = await self.get_vacancy_info(vacancy)
                vacancy_id = vacancy["vacancy_id"]

                if self.last_vacancy_id and self.last_vacancy_id == vacancy_id:
                    print("Dou stop\n")
                    is_stop = True
                    break

                if not self.last_vacancy_is_overriden:
                    await self.save_last_vacancy_id(vacancy_id)
                    self.last_vacancy_is_overriden = True

                if self.is_suitable_vacancy(vacancy["title"]):
                    await sync_to_async(Dou.objects.create)(**vacancy)

                    if self.is_first_vacancy_in_session:
                        self.is_first_vacancy_in_session = False

                        vacancy = await sync_to_async(Dou.objects.last)()
                        try:
                            first_vacancy = (
                                await sync_to_async(FirstVacancySession.objects.get)(spider_name=self.SPIDER_NAME)
                            )
                            first_vacancy.vacancy = vacancy.id
                            await sync_to_async(first_vacancy.save)()
                        except FirstVacancySession.DoesNotExist:
                            await sync_to_async(FirstVacancySession.objects.create)(
                                spider_name=self.SPIDER_NAME,
                                vacancy=vacancy.id
                            )

            if is_stop:
                break

            btn_click_more = await self.btn_more_click(page)
            if btn_click_more:
                await btn_click_more.click()
                print("Click btn more")
                time.sleep(0.3)
            else:
                break

    async def send_vacancies_to_bot(self):
        try:
            from_vacancy = await sync_to_async(FirstVacancySession.objects.get)(spider_name=self.SPIDER_NAME)
            if from_vacancy:
                vacancies: list[Dou] = (await sync_to_async(Dou.objects.filter)(
                    id__gte=from_vacancy.id
                )).order_by("publication_date")
                n_vacancy = 0
                async for vacancy in vacancies:
                    n_vacancy += 1
                    if n_vacancy == 29:
                        n_vacancy = 0
                        time.sleep(5)

                    await bot.send_message(
                        CHAT_ID,
                        text=f"{vacancy.url_to_vacancy} {vacancy.publication_date}",
                        disable_web_page_preview=True
                    )

                    vacancy.is_sent = True
                    await sync_to_async(vacancy.save)()

                await sync_to_async(from_vacancy.delete)()
            await bot.send_message(CHAT_ID, text="—————————————————————", disable_notification=True)
        except FirstVacancySession.DoesNotExist as ex:
            print(ex)

    async def start(self):
        print("Dou start")
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()
            await self.parse_vacancies(page)

            await context.close()
            await browser.close()


def main():
    DouSpider().start()


if __name__ == '__main__':
    main()
