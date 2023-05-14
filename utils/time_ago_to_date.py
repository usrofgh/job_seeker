import datetime


def get_date(time_ago: str) -> datetime.date:
    now = datetime.datetime.now()
    ago, unit_of_time = time_ago.split()[:2]
    ago = int(ago)
    if "секунд" in unit_of_time:
        now -= datetime.timedelta(seconds=ago)
    elif "хвилин" in unit_of_time:
        now -= datetime.timedelta(minutes=ago)
    elif "годин" in unit_of_time:
        now -= datetime.timedelta(hours=ago)
    elif unit_of_time in ["днів", "день", "дні"]:
        now -= datetime.timedelta(days=ago)
    elif "тижде" in unit_of_time:
        now -= datetime.timedelta(weeks=ago)
    else:
        now -= datetime.timedelta(weeks=4)

    return now
