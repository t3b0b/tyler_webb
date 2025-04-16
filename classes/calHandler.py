from datetime import datetime, timedelta
from extensions import db
from models import Event, Goals, Activity
from sqlalchemy.orm import aliased

class Calendar:
    def __init__(self):
        pass

    def generate_calendar_weeks(self, year, month):
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
    

    def prepWeekData(scores, events):
        """
        Konverterar score-objekt till en struktur med 'start_hour' och 'duration_in_hours'.
        """
        processed = {}

        for score in scores:
            date_str = score.Date.strftime('%Y-%m-%d')
            if date_str not in processed:
                processed[date_str] = []

            if score.activity_score:
                start_hour = score.Start.hour + score.Start.minute / 60
                duration = score.Time / 60  # omvandla till timmar

                processed[date_str].append({
                    'id': score.id,
                    'type': 'score',
                    'activity_name': score.activity_score.name,
                    'Start': score.Start,
                    'End': score.End,
                    'duration_hours': duration,
                    'minutes': score.Time
                })

        for event in events:
            date_str = event.date.strftime('%Y-%m-%d')
            if date_str not in processed:
                processed[date_str] = []

            if event.start_time is not None:
                start_hour = event.start_time.hour + event.start_time.minute / 60
                end_hour = event.end_time.hour + event.end_time.minute / 60 if event.end_time else start_hour + 1
                duration = end_hour - start_hour

                processed[date_str].append({
                    'id': event.id,
                    'type': 'event',
                    'event_name': event.name,
                    'Start': event.start_time,
                    'End': event.end_time,
                    'duration_hours': duration,
                    'location': event.location
                })

        return processed

class UserCalendar(Calendar):

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    def get_events_for_day(self, target_date):
        """Hämtar alla event för en viss dag inklusive återkommande events."""
        #target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        
        GoalAlias = aliased(Goals)
        ActivityAlias = aliased(Activity)

        # Hämta endast vanliga (icke-återkommande) events
        regular_events = db.session.query(
            Event,
            GoalAlias.name.label('goal_name'),
            ActivityAlias.name.label('activity_name')
        ).outerjoin(
            GoalAlias, Event.goal_id == GoalAlias.id
        ).outerjoin(
            ActivityAlias, Event.activity_id == ActivityAlias.id
        ).filter(
            (Event.user_id == self.user_id) & 
            (Event.date == target_date) & 
            (Event.is_recurring == False)
        ).all()

        # Hämta återkommande events
        recurring_events = db.session.query(
            Event,
            GoalAlias.name.label('goal_name'),
            ActivityAlias.name.label('activity_name')
        ).outerjoin(
            GoalAlias, Event.goal_id == GoalAlias.id
        ).outerjoin(
            ActivityAlias, Event.activity_id == ActivityAlias.id
        ).filter(
            (Event.user_id == self.user_id) & 
            (Event.is_recurring == True)
        ).all()

        valid_recurring_events = []
        
        for event, goal_name, activity_name in recurring_events:
            if event.recurrence_type == 'daily':
                if event.date <= target_date:
                    valid_recurring_events.append((event, goal_name, activity_name))
            elif event.recurrence_type == 'weekly':
                if event.date <= target_date and event.date.weekday() == target_date.weekday():
                    delta_days = (target_date - event.date).days
                    if delta_days % (event.recurrence_interval * 7) == 0:
                        valid_recurring_events.append((event, goal_name, activity_name))
            elif event.recurrence_type == 'monthly':
                if event.date.day == target_date.day and event.date <= target_date:
                    valid_recurring_events.append((event, goal_name, activity_name))

        # Kombinera vanliga och giltiga återkommande events
        print(valid_recurring_events)
        return regular_events + valid_recurring_events
        
    def get_weekly_events(self, start_week):

        recurring_events = Event.query.filter(
            (Event.is_recurring == 1),
            (Event.user_id == self.user_id)
        ).all()

        current_recurring_events = []

        for event in recurring_events:
            for i in range(7):
                potential_date = start_week + timedelta(days=i)
                if potential_date.weekday() ==  event.date.weekday():
                    event.date = potential_date.date()
                    current_recurring_events.append(event)

        return current_recurring_events
    
