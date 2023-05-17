import arrow
import pytz

import datetime


def vacancy_post_human_time_ago(vacancy) -> str:
    target_timezone = pytz.timezone("Europe/Kiev")

    try:
        date_of_vacancy = vacancy.publication_date.astimezone(target_timezone)
        now_with_utc = datetime.datetime.now().astimezone(target_timezone)
        vacancy_seconds_ago = (now_with_utc - date_of_vacancy).total_seconds()

    except AttributeError:
        today = datetime.datetime.today().date()
        if today == vacancy.publication_date:
            return "today"
        else:
            vacancy_seconds_ago = (today - vacancy.publication_date).total_seconds()

    human_ago = arrow.utcnow().shift(
        seconds=-vacancy_seconds_ago
    ).humanize()
    return human_ago
