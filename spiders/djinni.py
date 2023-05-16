import datetime
import time

from asgiref.sync import sync_to_async
from playwright.async_api import async_playwright

import init_django_module  # noqa F403


from spiders.SpiderBlueprint import AsyncSpiderBlueprint
from bot_info import bot, CHAT_ID
from vacancies.models import FirstVacancySession, Djinni


class DjinniSpider(AsyncSpiderBlueprint):
    BASE_URL = "https://djinni.co"
    SPIDER_NAME = "djinni_spider"
    URL = (
        "https://djinni.co/jobs/"
        "?keywords=python+-senior+-qa+-devops+-sysadmin"
        "&all-keywords="
        "&any-of-keywords="
        "&exclude-keywords="
        "&page=2"
    )
    DATE_FORMAT = "%d %B %Y"
    is_first_vacancy_in_session = True

    @staticmethod
    async def btn_next_page_click(page):
        is_last_btn_next = page.query_selector(".page-item.disabled")
        if is_last_btn_next:
            return None
        return is_last_btn_next

    async def get_vacancy_info(self, vacancy):
        vacancy_id = await (await vacancy.query_selector(".profile")).get_attribute("href")
        vacancy_id = vacancy_id.split("/")[2].split("-")[0]

        title = await (await vacancy.query_selector(".list__title a.profile span")).text_content()
        description = await (await vacancy.query_selector(".text-card")).text_content()
        salary_block = await vacancy.query_selector(".public-salary-item")
        url_to_vacancy = self.BASE_URL + await (await vacancy.query_selector("a.profile")).get_attribute("href")
        publication_date = await (await vacancy.query_selector(".text-date.order-2.ml-md-auto.pr-2.mb-2.mb-md-0.nowrap")).text_content()
        publication_date = publication_date.strip()

        if "сьогодні" in publication_date:
            publication_date = datetime.datetime.today()
        elif "вчора" in publication_date:
            publication_date = datetime.datetime.today() - datetime.timedelta(days=1)


        salary_from = None
        salary_to = None
        salary = None
        if salary_block is True:
            salary_text = await salary_block.text_content()
            if salary_text and "–" in salary_text:
                salary_text = salary_text.replace("$", "")
                salary_from, salary_to = [int(n) for n in salary_text.split("–")]
            else:
                salary = await salary_text.replace("$", "")

        return {
            "vacancy_id": vacancy_id,
            "title": title,
            "description": description,
            "salary_from": salary_from,
            "salary_to": salary_to,
            "salary": salary,
            "publication_date": publication_date,
            "url_to_vacancy": url_to_vacancy
        }

    async def parse_vacancies(self, page) -> None:
        await page.goto(self.URL)
        is_stop = False
        n_vac = 0
        self.last_vacancy_id = await sync_to_async(self.get_last_vacancy_id)()
        while True:
            await page.wait_for_selector(".list__item")
            vacancies = await page.query_selector_all(".list__item")
            vacancies = vacancies[n_vac::]
            for vacancy in vacancies:
                n_vac += 1

                vacancy = await self.get_vacancy_info(vacancy)
                vacancy_id = vacancy["vacancy_id"]

                if self.last_vacancy_id and self.last_vacancy_id == vacancy_id:
                    print("Djinni stop\n")
                    is_stop = True
                    break

                if not self.last_vacancy_is_overriden:
                    await self.save_last_vacancy_id(vacancy_id)
                    self.last_vacancy_is_overriden = True

                if self.is_suitable_vacancy(vacancy["title"]):
                    await sync_to_async(Djinni.objects.create)(**vacancy)

                    if self.is_first_vacancy_in_session:
                        self.is_first_vacancy_in_session = False

                        vacancy = await sync_to_async(Djinni.objects.last)()
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

            btn_click_more = await self.btn_next_page_click(page)
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
                vacancies: list[Djinni] = (await sync_to_async(Djinni.objects.filter)(
                    id__gte=from_vacancy.vacancy
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
        print("Djinni start")
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()
            await self.parse_vacancies(page)

            await context.close()
            await browser.close()


def main():
    DjinniSpider().start()


if __name__ == '__main__':
    main()
