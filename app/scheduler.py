from apscheduler.schedulers.background import BackgroundScheduler
from app.misiones.ranking_logic import sync_all_users_ranking


def init_scheduler(Session):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=sync_all_users_ranking,
        args=[Session],
        trigger='cron',
        day_of_week='sun',
        hour=23,
        minute=0
    )
    scheduler.start()
