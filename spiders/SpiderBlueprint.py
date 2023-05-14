from datetime import datetime

from asgiref.sync import sync_to_async

from utils.filter import EXCLUDE_WORDS, INCLUDE_WORDS
from utils.month_in_english import UA_MONTHS_TO_EU
from vacancies.models import LastVacancyId


class SpiderBlueprint:

    def __init__(self):
        self.last_vacancy_id = None
        self.last_vacancy_is_overriden = False

    def get_last_vacancy_id(self) -> int | None:
        try:
            return LastVacancyId.objects.get(spider_name=self.SPIDER_NAME).vacancy_id
        except LastVacancyId.DoesNotExist:
            return None

    def save_last_vacancy_id(self, vacancy_id: int) -> None:
        try:
            vacancy_meta = LastVacancyId.objects.get(spider_name=self.SPIDER_NAME)
            vacancy_meta.vacancy_id = vacancy_id
            vacancy_meta.save()

        except LastVacancyId.DoesNotExist:
            LastVacancyId.objects.create(
                spider_name=self.SPIDER_NAME,
                vacancy_id=vacancy_id
            )

    @staticmethod
    def is_suitable_vacancy(title: str) -> bool:
        is_there_excl_word = False
        is_there_incl_word = False

        for word in EXCLUDE_WORDS:
            if word in title.lower():
                is_there_excl_word = True
                break

        for word in INCLUDE_WORDS:
            if word in INCLUDE_WORDS:
                is_there_incl_word = True
                break

        return is_there_excl_word is False and is_there_incl_word is True

    def str_to_date(self, vacancy_date_str: str) -> datetime.date:
        month = vacancy_date_str.split(" ")[1]
        date_str = vacancy_date_str.replace(month, UA_MONTHS_TO_EU[month])
        date = datetime.strptime(date_str, self.DATE_FORMAT).date()
        return date


class AsyncSpiderBlueprint:
    def __init__(self):
        self.last_vacancy_id = None
        self.last_vacancy_is_overriden = False

    def get_last_vacancy_id(self) -> int | None:
        try:
            return LastVacancyId.objects.get(spider_name=self.SPIDER_NAME).vacancy_id
        except LastVacancyId.DoesNotExist:
            return None

    async def save_last_vacancy_id(self, vacancy_id: int) -> None:
        try:
            vacancy_meta = await sync_to_async(
                LastVacancyId.objects.get
            )(spider_name=self.SPIDER_NAME)
            vacancy_meta.vacancy_id = vacancy_id
            await sync_to_async(vacancy_meta.save)()

        except LastVacancyId.DoesNotExist:
            await sync_to_async(LastVacancyId.objects.create)(
                spider_name=self.SPIDER_NAME,
                vacancy_id=vacancy_id
            )

    @staticmethod
    def is_suitable_vacancy(title: str) -> bool:
        is_there_excl_word = False
        is_there_incl_word = False

        for word in EXCLUDE_WORDS:
            if word in title.lower():
                is_there_excl_word = True
                break

        for word in INCLUDE_WORDS:
            if word in INCLUDE_WORDS:
                is_there_incl_word = True
                break

        return is_there_excl_word is False and is_there_incl_word is True

    async def str_to_date(self, vacancy_date_str: str) -> datetime.date:
        month = vacancy_date_str.split(" ")[1]
        date_str = vacancy_date_str.replace(month, UA_MONTHS_TO_EU[month])
        date = datetime.strptime(date_str, self.DATE_FORMAT).date()
        return date
