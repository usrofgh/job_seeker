import time
from datetime import datetime

from asgiref.sync import sync_to_async

from bot_info import bot, CHAT_ID
from utils.filter import EXCLUDE_WORDS, INCLUDE_WORDS
from utils.month_in_english import UA_MONTHS_TO_ENG
from utils.time_ago_to_human import vacancy_post_human_time_ago
from vacancies.models import LastVacancyId, FirstVacancySession

MESSAGE_COUNTER = 0


class SendMessageToBotMixin:

    @classmethod
    async def send_vacancies_to_bot(cls):
        try:
            from_vacancy = await sync_to_async(
                FirstVacancySession.objects.get
            )(spider_name=cls.SPIDER_NAME)

            if from_vacancy:
                vacancies: list[cls.SPIDER_MODEL] = (
                    await sync_to_async(cls.SPIDER_MODEL.objects.filter)
                    (id__gte=from_vacancy.vacancy)
                ).order_by("publication_date")

                global MESSAGE_COUNTER
                async for vacancy in vacancies:
                    MESSAGE_COUNTER += 1
                    if MESSAGE_COUNTER == 25:
                        MESSAGE_COUNTER = 0
                        time.sleep(10)

                    await bot.send_message(
                        CHAT_ID,
                        text=f"[{cls.SPIDER_NAME}]({vacancy.url_to_vacancy}) "
                             f"{vacancy_post_human_time_ago(vacancy)}",
                        disable_web_page_preview=True,
                        parse_mode="Markdown"
                    )
                    vacancy.is_sent = True
                    await sync_to_async(vacancy.save)()

                await sync_to_async(from_vacancy.delete)()
            await bot.send_message(
                CHAT_ID,
                text="—————————————————————",
                disable_notification=True
            )
        except FirstVacancySession.DoesNotExist as ex:
            print(ex)


class FixFirstVacancyInSessionMixin:
    def fix_first_vacancy_in_session(self):
        if self.is_first_vacancy_in_session:
            self.is_first_vacancy_in_session = False

            vacancy = self.SPIDER_MODEL.objects.last()
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


class asyncFixFirstVacancyInSessionMixin:
    async def fix_first_vacancy_in_session(self):
        if self.is_first_vacancy_in_session:
            self.is_first_vacancy_in_session = False

            vacancy = await sync_to_async(self.SPIDER_MODEL.objects.last)()
            try:
                first_vacancy = (
                    await sync_to_async(FirstVacancySession.objects.get)
                    (spider_name=self.SPIDER_NAME)
                )
                first_vacancy.vacancy_id = vacancy.id
                sync_to_async(first_vacancy.save)()
            except FirstVacancySession.DoesNotExist:
                await sync_to_async(FirstVacancySession.objects.create)(
                    spider_name=self.SPIDER_NAME,
                    vacancy=vacancy.id
                )


class BaseSpider(SendMessageToBotMixin, FixFirstVacancyInSessionMixin):

    def __init__(self):
        self.last_vacancy_id = None
        self.last_vacancy_is_overriden = False
        self.is_first_vacancy_in_session = True

    def get_last_vacancy_id(self) -> int | None:
        try:
            return LastVacancyId.objects.get(
                spider_name=self.SPIDER_NAME
            ).vacancy_id

        except LastVacancyId.DoesNotExist:
            return None

    def save_last_vacancy_id(self, vacancy_id: int) -> None:
        try:
            vacancy_meta = LastVacancyId.objects.get(
                spider_name=self.SPIDER_NAME
            )

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
        date_str = vacancy_date_str.replace(month, UA_MONTHS_TO_ENG[month])
        date = datetime.strptime(date_str, self.DATE_FORMAT).date()
        return date


class AsyncBaseSpider(SendMessageToBotMixin, asyncFixFirstVacancyInSessionMixin):

    def __init__(self):
        self.last_vacancy_id = None
        self.last_vacancy_is_overriden = False
        self.is_first_vacancy_in_session = True

    def get_last_vacancy_id(self) -> int | None:
        try:
            return LastVacancyId.objects.get(
                spider_name=self.SPIDER_NAME
            ).vacancy_id
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
        date_str = vacancy_date_str.replace(month, UA_MONTHS_TO_ENG[month])
        date = datetime.strptime(date_str, self.DATE_FORMAT).date()
        return date
