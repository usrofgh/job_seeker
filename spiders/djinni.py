import datetime

import requests
from bs4 import BeautifulSoup

import init_django_module  # noqa F403


from spiders.SpiderBlueprint import BaseSpider
from vacancies.models import Djinni


class DjinniSpider(BaseSpider):
    BASE_URL = "https://djinni.co"
    SPIDER_NAME = "djinni_spider"
    SPIDER_MODEL = Djinni
    DATE_FORMAT = "%d %B %Y"
    URL = (
        "https://djinni.co/jobs/"
        "?keywords=python+-senior+-qa+-devops+-sysadmin"
        "&all-keywords="
        "&any-of-keywords="
        "&exclude-keywords="
    )

    def get_vacancy_info(self, vacancy):
        vacancy_id = vacancy.select_one(".profile")["href"].split("/")[2].split("-")[0]

        company_name = vacancy.select_one(".list-jobs__details__info a").text.strip()
        title = vacancy.select_one(".list__title a.profile span").text.strip()
        description = vacancy.select_one(".text-card").text.strip()
        location_work = " ".join(vacancy.select_one(".location-text .bi").next_element.strip().split())
        space_work = vacancy.select_one(".bi-building").next_element.strip()
        url_to_vacancy = self.BASE_URL + vacancy.select_one("a.profile")["href"]
        publication_date = vacancy.select_one(".text-date.order-2.ml-md-auto.pr-2.mb-2.mb-md-0.nowrap").text
        publication_date = "сьогодні" if "сьогодні" in publication_date else "вчора"
        today_date = datetime.datetime.today()
        if "сьогодні" in publication_date:
            publication_date = today_date
        else:
            publication_date = today_date - datetime.timedelta(days=1)

        salary_block = vacancy.select_one(".public-salary-item")
        salary_from = None
        salary_to = None
        salary = None
        if salary_block is True:
            salary_text = salary_block.text
            if salary_text and "–" in salary_text:
                salary_text = salary_text.replace("$", "")
                salary_from, salary_to = [int(n) for n in salary_text.split("–")]
            else:
                salary = salary_text.replace("$", "")

        return {
            "vacancy_id": vacancy_id,
            "company_name": company_name,
            "location_work": location_work,
            "space_work": space_work,
            "title": title,
            "description": description,
            "salary_from": salary_from,
            "salary_to": salary_to,
            "salary": salary,
            "publication_date": publication_date,
            "url_to_vacancy": url_to_vacancy
        }

    def get_vacancy_list(self, soup) -> None:
        is_stop = False
        self.last_vacancy_id = self.get_last_vacancy_id()
        vacancies = soup.select(".list__item")
        for vacancy in vacancies:
            vacancy_info = self.get_vacancy_info(vacancy)

            vacancy_id = vacancy_info["vacancy_id"]
            if self.last_vacancy_id and self.last_vacancy_id == vacancy_id:
                print("Djinni stop\n")
                is_stop = True
                break

            if not self.last_vacancy_is_overriden:
                self.save_last_vacancy_id(vacancy_id)
                self.last_vacancy_is_overriden = True

            if not self.is_suitable_vacancy(vacancy_info["title"]):
                continue

            self.SPIDER_MODEL.objects.create(**vacancy_info)
            self.fix_first_vacancy_in_session()

        if is_stop:
            return

    def start(self):
        print("Djinni start")
        print(f"request to #1 page")

        response = requests.get(self.URL)
        soup = BeautifulSoup(response.content, "html.parser")
        last_page = int(soup.select(".page-link")[-2]["href"].split("=")[-1])

        for n_page in range(1, last_page):
            next_page = self.URL + f"&page={n_page}"
            print(f"request to #{n_page} page")
            response = requests.get(next_page)
            soup = BeautifulSoup(response.content, "html.parser")
            self.get_vacancy_list(soup)

