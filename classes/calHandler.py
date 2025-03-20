from datetime import datetime, timedelta

class Calendar:
    def __init__():
        pass

# region Calendar
    def generate_calendar_weeks(year, month):
        first_day_of_month = datetime(year, month, 1)
        days = []
        string_day = []
        # Föregående månad
        previous_month_day = first_day_of_month - timedelta(days=1)

        while previous_month_day.weekday() != 6:  # Söndag är 6 i weekday() funktionen
            days.insert(0, {'day': previous_month_day.day, 'date': previous_month_day, 'current_month': False})
            previous_month_day -= timedelta(days=1)

        # Aktuell månad
        current_day = first_day_of_month
        while current_day.month == month:
            days.append({'day': current_day.day, 'date': current_day, 'current_month': True})
            current_day += timedelta(days=1)

        # Nästkommande månad
        while len(days) % 7 != 0:
            days.append({'day': current_day.day, 'date': current_day, 'current_month': False})

            current_day += timedelta(days=1)
            string_day.append(current_day)
        # Dela upp dagarna i veckor
        weeks = [days[i:i + 7] for i in range(0, len(days), 7)]

        return weeks
# endregion