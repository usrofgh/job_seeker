from asgiref.sync import sync_to_async
from django.db import models


class WorkUa(models.Model):
    title = models.CharField(max_length=300)
    company_name = models.CharField(max_length=200)
    vacancy_id = models.CharField(max_length=100)
    location_work = models.CharField(max_length=200, null=True)
    distance_to_center_in_km = models.FloatField(null=True)
    salary_from = models.IntegerField(null=True)
    salary_to = models.IntegerField(null=True)
    salary = models.IntegerField(null=True)

    publication_date = models.DateField()

    @property
    def url_to_vacancy(self) -> str:
        return f"https://www.work.ua/jobs/{self.vacancy_id}/"

    @sync_to_async
    def get_5_vacancies(self) -> list["WorkUa"]:
        return WorkUa.objects.all()[:5]


class RabotaUa(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField()
    company_name = models.CharField(max_length=200)
    company_id = models.IntegerField()
    vacancy_id = models.CharField(max_length=100)
    location_work = models.CharField(max_length=200, null=True)
    salary_from = models.IntegerField(null=True)
    salary_to = models.IntegerField(null=True)
    salary = models.IntegerField(null=True)
    comment_to_salary = models.CharField(max_length=255, null=True)

    publication_date = models.DateField()

    @property  # TODO: check it
    def url_to_vacancy(self) -> str:
        return f"https://rabota.ua/ua/company{self.company_id}/vacancy{self.vacancy_id}/"


class Dou(models.Model):
    vacancy_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=300)
    company_name = models.CharField(max_length=300)
    location_work = models.CharField(max_length=300)
    salary_from = models.IntegerField(null=True)
    salary_to = models.IntegerField(null=True)
    salary = models.IntegerField(null=True)
    description = models.TextField()
    url_to_vacancy = models.CharField(max_length=500, unique=True)

    publication_date = models.DateField()


class Djinni(models.Model):
    vacancy_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=300)
    company_name = models.CharField(max_length=300)
    description = models.CharField(max_length=500)
    url_to_vacancy = models.CharField(max_length=500, unique=True)
    salary_from = models.IntegerField(null=True)
    salary_to = models.IntegerField(null=True)
    salary = models.IntegerField(null=True)
    publication_date = models.DateField()



class LastVacancyId(models.Model):
    spider_name = models.CharField(unique=True, max_length=50)
    vacancy_id = models.IntegerField()


class Telegram(models.Model):
    vacancy_id = models.IntegerField()
    spider_name = models.CharField(max_length=255)
    publication_date = models.DateTimeField()
    description = models.TextField()

    is_sent = models.BooleanField(default=False)
    is_viewed = models.BooleanField(default=False)
    is_not_want = models.BooleanField(null=True)

    @property
    def url_to_vacancy(self) -> str:
        return f"t.me/{self.spider_name}/{self.vacancy_id}"

    @property
    def publication_date_time(self):
        return f"{self.publication_date.time()}"

    @property
    def publication_date_date(self):
        return f"{self.publication_date.date()}"

    def __str__(self):
        return f"{self.spider_name} {self.vacancy_id}"

    class Meta:
        unique_together = ("vacancy_id", "spider_name")


class TelegramLastVacancyId(models.Model):
    spider_name = models.CharField(unique=True, max_length=100)
    vacancy_id = models.IntegerField(unique=True)

    @property
    def url_to_vacancy(self) -> str:
        if isinstance(self.spider_name, str):
            return f"t.me/{self.spider_name}/{self.vacancy_id}"
        return f"t.me/c/{self.spider_name}/{self.vacancy_id}"

    def __str__(self):
        return f"{self.spider_name} {self.vacancy_id}"


class FirstVacancySession(models.Model):
    spider_name = models.CharField(max_length=255, unique=True)
    vacancy = models.IntegerField()
