from django.db import models


class BaseModel(models.Model):
    vacancy_id = models.CharField(max_length=100)
    company_name = models.CharField(max_length=200)
    location_work = models.CharField(max_length=200, null=True)
    title = models.CharField(max_length=300)
    description = models.TextField()

    salary_from = models.IntegerField(null=True)
    salary_to = models.IntegerField(null=True)
    salary = models.IntegerField(null=True)

    publication_date = models.DateField(null=True)

    class Meta:
        abstract = True


class WorkUa(BaseModel):
    distance_to_center_in_km = models.FloatField(null=True)

    @property
    def url_to_vacancy(self) -> str:
        return f"https://www.work.ua/jobs/{self.vacancy_id}/"


class RabotaUa(BaseModel):
    company_id = models.IntegerField()
    comment_to_salary = models.CharField(max_length=255, null=True)

    @property
    def url_to_vacancy(self) -> str:
        return (
            f"https://rabota.ua/ua/company"
            f"{self.company_id}"
            f"/vacancy{self.vacancy_id}/"
        )


class Dou(BaseModel):
    url_to_vacancy = models.CharField(max_length=500, unique=True)


class Djinni(BaseModel):
    space_work = models.CharField(max_length=100)
    url_to_vacancy = models.CharField(max_length=500, unique=True)


class Telegram(models.Model):
    vacancy_id = models.IntegerField()
    spider_name = models.CharField(max_length=255)
    publication_date = models.DateTimeField()
    description = models.TextField()

    is_sent = models.BooleanField(default=False)

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


class LastVacancyId(models.Model):
    spider_name = models.CharField(unique=True, max_length=50)
    vacancy_id = models.IntegerField()


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
