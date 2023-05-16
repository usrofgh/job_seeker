import asyncio
import time

import requests as requests
from asgiref.sync import sync_to_async

import init_django_module  # noqa F403


from bs4 import BeautifulSoup

from urllib.parse import urljoin, urlencode

from spiders.SpiderBlueprint import SpiderBlueprint
from spiders.telegram import bot, CHAT_ID
from vacancies.models import WorkUa, FirstVacancySession


class WorkUaSpider(SpiderBlueprint):
    SPIDER_NAME = "work_ua"
    BASE_URL = "https://www.work.ua/jobs-python/"
    DATE_FORMAT = "%d %B %Y"
    is_first_vacancy_in_session = True

    def get_vacancy_list(self, soup: BeautifulSoup):
        is_stop = False
        self.last_vacancy_id = self.get_last_vacancy_id()
        for vacancy in soup.select(".card.card-hover"):
            vacancy_id = int(vacancy.select_one("h2 a")["href"].split("/")[-2])
            if self.last_vacancy_id and vacancy_id == self.last_vacancy_id:
                print("WorkUa stop\n")
                is_stop = True
                break

            if not self.last_vacancy_is_overriden:
                self.save_last_vacancy_id(vacancy_id)
                self.last_vacancy_is_overriden = True

            title, publication_date = (
                vacancy.select_one("h2 a")["title"]
                .split(", вакансія від ")
            )

            if not self.is_suitable_vacancy(title):
                continue

            publication_date = self.str_to_date(publication_date)
            company_name = vacancy.select_one(".add-top-xs span b").text

            distance_to_center_in_km = (
                vacancy.select_one(".add-top-xs .distance-block span .bp-more.nowrap")
            )  # or None

            if distance_to_center_in_km:
                distance_to_center_in_km = (
                    distance_to_center_in_km.text
                    .strip()
                    .replace('\xa0', ' ')
                    .replace(",", ".")
                    .split(" ")[0]
                )
                location_work = vacancy.select(".add-top-xs span")[-4].text
            else:
                location_work = vacancy.select(".add-top-xs span")[-1].text

            salary_block = vacancy.select_one("div b").text
            salary_from = None
            salary_to = None
            salary = None

            if "–" in salary_block:
                salary_from, salary_to = (
                    salary_block
                    .replace("\u202f", " ")
                    .replace("\u2009", " ").replace("\xa0грн", "")
                    .replace(" ", "").split("–")
                )
            elif "грн" in salary_block:
                salary = salary_block.replace('\u202f', "").replace('\xa0грн', "").replace(" ", "")

            res = {
                "title": title,
                "publication_date": publication_date,
                "vacancy_id": vacancy_id,
                "company_name": company_name,
                "location_work": location_work,
                "distance_to_center_in_km": distance_to_center_in_km,
                "salary_from": salary_from,
                "salary_to": salary_to,
                "salary": salary,
            }
            WorkUa.objects.create(**res)

            if self.is_first_vacancy_in_session:
                self.is_first_vacancy_in_session = False

                vacancy = WorkUa.objects.last()
                try:
                    first_vacancy = (
                        FirstVacancySession.objects.get(spider_name=self.SPIDER_NAME)
                    )
                    first_vacancy.vacancy = vacancy.id
                    first_vacancy.save()
                except FirstVacancySession.DoesNotExist:
                    FirstVacancySession.objects.create(
                        spider_name=self.SPIDER_NAME,
                        vacancy=vacancy.id
                    )

        if is_stop:
            return

        try:
            last_page = soup.select_one(".pagination.hidden-xs").select("li")[-1].select_one("a")["href"]
        except TypeError:
            print("WorkUa stop\n")
            last_page = None

        if last_page:
            next_page = (
                last_page
                .split("=")[1]
                .split("&")[0]
            )
            next_page = urljoin(self.BASE_URL, "?" + urlencode({"page": next_page}))
            print(f"request to #{next_page} page")
            response = requests.get(next_page)
            soup = BeautifulSoup(response.content, "html.parser")
            self.get_vacancy_list(soup)

    async def send_vacancies_to_bot(self):
        try:
            from_vacancy = await sync_to_async(FirstVacancySession.objects.get)(spider_name=self.SPIDER_NAME)
            if from_vacancy:
                vacancies: list[WorkUa] = (await sync_to_async(WorkUa.objects.filter)(
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

    def start(self):
        print("WorkUa start")
        response = requests.get(self.BASE_URL)
        print(f"request to #1 page")
        soup = BeautifulSoup(response.content, "html.parser")

        self.get_vacancy_list(soup)


def main():
    WorkUaSpider().start()


if __name__ == '__main__':
    main()
