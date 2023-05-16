# Generated by Django 4.2 on 2023-05-14 13:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Dou",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("vacancy_id", models.IntegerField(unique=True)),
                ("title", models.CharField(max_length=300)),
                ("company_name", models.CharField(max_length=300)),
                ("location_work", models.CharField(max_length=300)),
                ("salary_from", models.IntegerField(null=True)),
                ("salary_to", models.IntegerField(null=True)),
                ("salary", models.IntegerField(null=True)),
                ("description", models.TextField()),
                ("publication_date", models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name="LastVacancyId",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("spider_name", models.CharField(max_length=50, unique=True)),
                ("vacancy_id", models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name="RabotaUa",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=300)),
                ("description", models.TextField()),
                ("company_name", models.CharField(max_length=200)),
                ("company_id", models.IntegerField()),
                ("vacancy_id", models.CharField(max_length=100)),
                ("location_work", models.CharField(max_length=200, null=True)),
                ("salary_from", models.IntegerField(null=True)),
                ("salary_to", models.IntegerField(null=True)),
                ("salary", models.IntegerField(null=True)),
                ("comment_to_salary", models.CharField(max_length=255, null=True)),
                ("publication_date", models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name="TelegramLastVacancyId",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("spider_name", models.CharField(max_length=100, unique=True)),
                ("vacancy_id", models.IntegerField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="WorkUa",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=300)),
                ("company_name", models.CharField(max_length=200)),
                ("vacancy_id", models.CharField(max_length=100)),
                ("location_work", models.CharField(max_length=200, null=True)),
                ("distance_to_center_in_km", models.FloatField(null=True)),
                ("salary_from", models.IntegerField(null=True)),
                ("salary_to", models.IntegerField(null=True)),
                ("salary", models.IntegerField(null=True)),
                ("publication_date", models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name="Telegram",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("vacancy_id", models.IntegerField()),
                ("spider_name", models.CharField(max_length=255)),
                ("publication_date", models.DateTimeField()),
                ("description", models.TextField()),
                ("is_sent", models.BooleanField(default=False)),
                ("is_viewed", models.BooleanField(default=False)),
                ("is_not_want", models.BooleanField(null=True)),
            ],
            options={
                "unique_together": {("vacancy_id", "spider_name")},
            },
        ),
        migrations.CreateModel(
            name="FirstVacancySession",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("spider_name", models.CharField(max_length=255, unique=True)),
                (
                    "vacancy",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="first_vacancy_session",
                        to="vacancies.telegram",
                    ),
                ),
            ],
        ),
    ]
