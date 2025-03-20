from datetime import datetime, timedelta
from extensions import db
from models import Event, Goals
from sqlalchemy.orm import aliased

class Calendar:
    def __init__():
        pass

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
    

class UserCalendar(Calendar):

    def __init__(self, user_id):
        super.__init__()
        self.user_id = user_id
    
    def get_events_for_day(self, target_date):
        """Hämtar alla event för en viss dag inklusive återkommande events."""
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        
        myGoals = Goals.query.filter_by(user_id=self.user_id)
        Goal = aliased(Goals)

        # Hämta alla event (både vanliga och återkommande)
        db.session.query(
            Event.id.label('event_id')

        )
        events = Event.query.filter(
            (Event.user_id == self.user_id) & 
            ((Event.date == target_date) | (Event.is_recurring == True))
        ).all()

        recurring_events = []
        
        for event in events:
            if event.is_recurring:
                if event.recurrence_type == 'daily':
                    if event.date <= target_date:
                        recurring_events.append(event)
                elif event.recurrence_type == 'weekly':
                    delta_days = (target_date - event.date).days
                    if delta_days % event.recurrence_interval == 0:
                        recurring_events.append(event)
                elif event.recurrence_type == 'monthly':
                    if event.date.day == target_date.day and event.date <= target_date:
                        recurring_events.append(event)

        return events + recurring_events
