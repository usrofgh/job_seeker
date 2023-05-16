import time

from asgiref.sync import sync_to_async

import init_django_module  # noqa F403

import json

import requests

from spiders.SpiderBlueprint import SpiderBlueprint
from spiders.telegram import bot, CHAT_ID
from utils.time_ago_to_date import get_date
from vacancies.models import RabotaUa, FirstVacancySession


class RabotaUaSpiser(SpiderBlueprint):
    SPIDER_NAME = "rabota_ua"
    BASE_URL = "https://dracula.rabota.ua/?q=getPublishedVacanciesList"
    is_first_vacancy_in_session = True

    def get_api_page_list(self, n_page: int):
        payload = json.dumps({
            "operationName": "getPublishedVacanciesList",
            "variables": {
                "pagination": {
                    "count": 40,
                    "page": n_page
                },
                "filter": {
                    "keywords": "python"
                },
                "sort": "BY_DATE"
            },
            "query": "query getPublishedVacanciesList($filter: PublishedVacanciesFilterInput!, $pagination: PublishedVacanciesPaginationInput!, $sort: PublishedVacanciesSortType!) {\n  publishedVacancies(filter: $filter, pagination: $pagination, sort: $sort) {\n    totalCount\n    items {\n      ...PublishedVacanciesItem\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment PublishedVacanciesItem on Vacancy {\n  id\n  schedules {\n    id\n    __typename\n  }\n  title\n  description\n  sortDateText\n  hot\n  designBannerUrl\n  badges {\n    name\n    __typename\n  }\n  salary {\n    amount\n    comment\n    amountFrom\n    amountTo\n    __typename\n  }\n  company {\n    id\n    logoUrl\n    name\n    __typename\n  }\n  city {\n    id\n    name\n    __typename\n  }\n  showProfile\n  seekerFavorite {\n    isFavorite\n    __typename\n  }\n  seekerDisliked {\n    isDisliked\n    __typename\n  }\n  formApplyCustomUrl\n  anonymous\n  isActive\n  publicationType\n  __typename\n}\n"
        })
        headers = {
            'authority': 'dracula.rabota.ua',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'uk',
            'apollographql-client-name': 'web-alliance-desktop',
            'apollographql-client-version': 'dae4050',
            'content-type': 'application/json',
            'origin': 'https://rabota.ua',
            'referer': 'https://rabota.ua/',
            'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
        }

        return requests.post(self.BASE_URL, headers=headers, data=payload)

    def start(self):
        print("RabotaUa start")
        is_stop = False
        page_n = 0
        while True:
            print(f"request to #{page_n + 1} page")
            info = self.get_api_page_list(page_n)
            info = dict(info.json())
            vacancies = info["data"]["publishedVacancies"]["items"]
            if len(vacancies) == 0:
                print("RabotaUa stop\n")
                break

            self.last_vacancy_id = self.get_last_vacancy_id()

            for vacancy in vacancies:
                title = vacancy["title"].strip()
                vacancy_id = int(vacancy["id"])
                if self.last_vacancy_id and vacancy_id == self.last_vacancy_id:
                    print("RabotaUa stop\n")
                    is_stop = True
                    break

                if not self.last_vacancy_is_overriden:
                    self.save_last_vacancy_id(vacancy_id)
                    self.last_vacancy_is_overriden = True

                if self.is_suitable_vacancy(title) is False:
                    continue

                short_description = vacancy["description"].strip()
                publication_ago = vacancy["sortDateText"].strip()
                salary = vacancy["salary"]["amount"]
                salary_from = vacancy["salary"]["amountFrom"]
                salary_to = vacancy["salary"]["amountTo"]
                comment_to_salary = vacancy["salary"]["comment"]
                company_id = vacancy["company"]["id"]
                company_name = vacancy["company"]["name"]
                city = vacancy["city"]["name"]

                RabotaUa.objects.create(
                    title=title,
                    description=short_description,
                    company_name=company_name,
                    company_id=company_id,
                    vacancy_id=vacancy_id,
                    location_work=city,
                    salary=salary,
                    salary_from=salary_from,
                    salary_to=salary_to,
                    comment_to_salary=comment_to_salary,
                    publication_date=get_date(publication_ago)
                )

                if self.is_first_vacancy_in_session:
                    self.is_first_vacancy_in_session = False

                    vacancy = RabotaUa.objects.last()
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
                break
            page_n += 1

    async def send_vacancies_to_bot(self):
        try:
            from_vacancy = await sync_to_async(FirstVacancySession.objects.get)(spider_name=self.SPIDER_NAME)
            if from_vacancy:
                vacancies: list[RabotaUa] = (await sync_to_async(RabotaUa.objects.filter)(
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


def main():
    RabotaUaSpiser().start()


if __name__ == '__main__':
    main()
