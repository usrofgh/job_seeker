import init_django_module  # noqa F403

import requests as requests

from bs4 import BeautifulSoup

from urllib.parse import urljoin, urlencode

from spiders.SpiderBlueprint import BaseSpider
from utils.user_agents import USER_AGENTS_ITER
from vacancies.models import WorkUa


class WorkUaSpider(BaseSpider):
    SPIDER_NAME = "work_ua"
    SPIDER_MODEL = WorkUa
    BASE_URL = "https://www.work.ua/jobs-python/"
    DATE_FORMAT = "%d %B %Y"

    def get_vacancy_list(self, soup: BeautifulSoup):
        is_stop = False
        self.last_vacancy_id = self.get_last_vacancy_id()
        vacancies = soup.select(".card.card-hover")
        for vacancy in vacancies:
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
            )

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
            self.SPIDER_MODEL.objects.create(**res)
            self.fix_first_vacancy_in_session()

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

    def start(self):
        print("WorkUa start")
        response = requests.get(self.BASE_URL, headers=next(USER_AGENTS_ITER))
        print(f"request to #1 page")
        soup = BeautifulSoup(response.content, "html.parser")

        self.get_vacancy_list(soup)
