from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from models import Notification, db

def delete_old_notifications():
    cutoff = datetime.utcnow() - timedelta(days=30)
    deleted = Notification.query.filter(Notification.created_at < cutoff).delete()
    db.session.commit()
    print(f"Deleted {deleted} old notifications.")

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(delete_old_notifications, 'interval', hours=24)  # Kör varje dag
    print("Scheduler is running. Press Ctrl+C to exit.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
