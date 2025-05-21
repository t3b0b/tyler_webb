from datetime import datetime, timedelta
from calendar import monthrange
from models import Score, Goals, Activity, User
from extensions import db
from models import MyWords

class ScoreAnalyzer:
    def __init__(self):
        pass

    def sumGoal(self, score_list):
        goal_summary = {}
        for row in score_list:
            goal_name = row.goalName or 'Okänt mål'  # Hantera None
            time = row.Time or 0                     # Hantera None

            if goal_name not in goal_summary:
                goal_summary[goal_name] = 0

            goal_summary[goal_name] += time

        return goal_summary

    def sumDays(self, score):
        daySum = {}
        for row in score:
            day = row.Date
            time = row.Time or 0  # Om time är None, ersätt med 0
            if day not in daySum:
                daySum[day] = 0  # 🟢 Initiera med 0 om dagen inte finns
            daySum[day] += time  # Lägg till tiden för den dagen

        return daySum

    def sumAct(self, score):
        actSum = {}
        for row in score:
            actName=row.actName
            time=row.Time or 0
            
            if actName not in actSum:
                actSum[actName] = 0
            
            actSum[actName] += time
        return actSum


class UserScores(ScoreAnalyzer):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
    
    def get_weekly_scores(self):

        today = datetime.now()  # Byt från utcnow() till now()
        start_of_this_week = today - timedelta(days=today.weekday())  # Får måndag denna vecka (kl 00:00)
        start_of_last_week = start_of_this_week - timedelta(days=7)  # Måndag förra veckan
        end_of_last_week = start_of_this_week - timedelta(days=1)  # Söndag förra veckan
        
        # Hämta poäng från databasen
        this_week_scores = db.session.query(
            Score.Date, db.func.sum(Score.Time).label('total_points')
        ).filter(
            Score.user_id == self.user_id,
            Score.Date >= start_of_this_week.date(),  # Fixar måndagsproblemet
            Score.Date <= today.date()  # Endast till idag, ej framtida poster
        ).group_by(Score.Date).all()

        last_week_scores = db.session.query(
            Score.Date, db.func.sum(Score.Time).label('total_points')
        ).filter(
            Score.user_id == self.user_id,
            Score.Date >= start_of_last_week.date(),  # Använder .date() för att jämföra rätt
            Score.Date <= end_of_last_week.date()
        ).group_by(Score.Date).all()

        activity_times = db.session.query(
            Activity.name,
            db.func.sum(Score.Time).label('total_time')
        ).join(Score).filter(
            Score.user_id == self.user_id,
            Score.Date.between(start_of_this_week.date(), today.date())
        ).group_by(Activity.name).all()

        return this_week_scores, last_week_scores, activity_times

    def get_all_goal_scores(self,start_date=None,end_date=None):
        result = db.session.query(
            Goals.name.label('goal_name'),
            db.func.sum(Score.Time).label('total_time')
        ).join(Score, Goals.id == Score.goal_id
        ).group_by(Goals.name
        ).order_by(db.func.sum(Score.Time).desc()
        ).all()

        return result
    
    '''   if start_date is None and end_date is None :
            goals = Goals.query.filter_by(user_id = self.user_id
                    ).join(Score
                    ).filter(Score.Date >= start_date,
                            Score.Date <= end_date
                    ).all()
        else:
            goals = Goals.query.filter_by(user_id=self.user_id)
        
        for goal s

        if start_date:
        goal_list = []
        for goal in goals:
            key = goal.name
'''


    def get_goal_scores(self, goal_id):
        goal = Goals.query.get(goal_id)
        goal_scores = goal.scores
        tot = 0
        
        for score in goal_scores:
            if score.activity_id != None:
                tot += score.Time
        return tot
    
    def get_activity_scores(self, activity_id):
        activity = Activity.query.get(activity_id)
        activity_scores = activity.scores
        tot = 0
        for score in activity_scores:
            tot += score.Time
        return tot

    def get_average_scores(self, period='week', reference_date=None):
        """
        Beräknar medelvärdet av poäng per vecka eller månad.
        :param period: 'week' eller 'month'
        :param reference_date: Datum att basera beräkningen på (standard är idag)
        :return: Medelvärde för perioden
        """
        today = datetime.now().date()

        if reference_date is None:
            reference_date = today
        elif isinstance(reference_date, datetime):
            reference_date = reference_date.date()

        if period == 'week':
            start_date = reference_date - timedelta(days=reference_date.weekday())
            end_date = min(today, start_date + timedelta(days=6))  # Söndag denna vecka eller idag
        elif period == 'month':
            start_date = reference_date.replace(day=1)
            last_day = monthrange(reference_date.year, reference_date.month)[1]
            end_date = min(today, reference_date.replace(day=monthrange(reference_date.year, reference_date.month)[1]))  # Sista dagen i månaden eller idag
        else:
            raise ValueError("Ogiltig period. Välj 'week' eller 'month'.")

        scores = db.session.query(
            db.func.sum(Score.Time).label('total_time'),
        ).filter(
            Score.user_id == self.user_id,
            Score.Date >= start_date,
            Score.Date <= end_date
        ).first()

        total_time = scores.total_time or 0
        days_count = (end_date - start_date).days + 1  # Antal dagar i perioden (inklusive idag)

        # Beräkna medelvärde
        average = total_time / days_count if days_count > 0 else 0

        return {
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "total_time": total_time,
            "average": round(average)
        }
    
    def get_scores_by_period(self, period='week', reference_date=None):
        today = datetime.now().date()

        if reference_date is None:
            reference_date = today
        elif isinstance(reference_date, datetime):
            reference_date = reference_date.date()

        if period == 'week':
            start_date = reference_date - timedelta(days=reference_date.weekday())
            # Om vi är i aktuell vecka, sluta idag, annars söndag den veckan
            if reference_date.isocalendar()[1] == today.isocalendar()[1] and reference_date.year == today.year:
                end_date = today
            else:
                end_date = start_date + timedelta(days=6)  # Söndag samma vecka

        elif period == 'month':
            # Första dagen i månaden
            start_date = reference_date.replace(day=1)
            # Om samma månad och år som idag, sluta idag, annars sista dagen i månaden
            if reference_date.month == today.month and reference_date.year == today.year:
                end_date = today
            else:
                last_day = monthrange(reference_date.year, reference_date.month)[1]  # Sista dagen i månaden
                end_date = reference_date.replace(day=last_day)

        elif period == 'year':
            # Första januari
            start_date = reference_date.replace(month=1, day=1)
            # Om samma år, sluta idag, annars 31 december
            if reference_date.year == today.year:
                end_date = today
            else:
                end_date = reference_date.replace(month=12, day=31)
        else:
            raise ValueError("Ogiltig period. Välj 'week', 'month', eller 'year'.")

        # 🔽 Debug utskrift om du vill se datumen (kan tas bort)
        print(f"Period: {period}, Start: {start_date}, End: {end_date}")

        # Hämta poäng från Score
        scores = db.session.query(
            Score.Time.label('Time'),              # Poäng/tid
            Score.Date.label('Date'),              # Datum
            Goals.name.label('goalName'),         # Mål-namn
            Activity.name.label('actName')   # Aktivitet-namn
        ).outerjoin(
            Goals, Goals.id == Score.goal_id
        ).outerjoin(
            Activity, Activity.id == Score.activity_id
        ).filter(
            Score.user_id == self.user_id,
            Score.Date >= start_date,
            Score.Date <= end_date
        ).all()

            # Hämta aktivitetstider per aktivitet inom samma period
        activity_times = db.session.query(
            Activity.name.label('activity_name'),          # Namnet på aktiviteten
            Goals.name.label('goal_name'),                # Namnet på målet som aktiviteten tillhör
            db.func.sum(Score.Time).label('total_time')   # Summan av tid för aktiviteten
        ).join(
            Score, Score.activity_id == Activity.id          # Join till Score baserat på aktiviteten
        ).outerjoin(
            Goals, Goals.id == Activity.goal_id           # Join till Goals baserat på goal_id
        ).filter(
            Score.user_id == self.user_id,
            Score.Date >= start_date,
            Score.Date <= end_date
        ).group_by(
            Activity.name, Goals.name                    # Gruppera både på aktivitet och mål
        ).all()
        
        return scores, activity_times
    
    def myDayScore(self, day_offset=0):
        # Beräkna streaks-poäng
        date = datetime.now().date() - timedelta(days=day_offset)

        streak_points = db.session.query(db.func.sum(Score.Time)).filter(
            Score.user_id == self.user_id,
            db.func.date(Score.Date) == date,
            Score.activity_id == None  # Streaks har ingen aktivitet kopplad
        ).scalar() or 0

        # Beräkna aktivitetspoäng
        activity_points = db.session.query(db.func.sum(Score.Time)).filter(
            Score.user_id == self.user_id,
            db.func.date(Score.Date) == date,
            Score.activity_id != None  # Poäng kopplade till aktiviteter
        ).scalar() or 0

        # Totalpoäng
        total_points = streak_points + activity_points

        # Returnera totalpoäng och en ordbok med detaljer
        return total_points, {
            "streak_points": streak_points,
            "activity_points": activity_points
        }
