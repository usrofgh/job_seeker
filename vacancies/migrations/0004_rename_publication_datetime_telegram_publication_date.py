# Generated by Django 4.2 on 2023-05-15 17:13

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("vacancies", "0003_djinni_dou_url_to_vacancy"),
    ]

    operations = [
        migrations.RenameField(
            model_name="telegram",
            old_name="publication_date",
            new_name="publication_date",
        ),
    ]
