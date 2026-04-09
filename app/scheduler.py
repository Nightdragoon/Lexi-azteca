from apscheduler.schedulers.background import BackgroundScheduler
from app.misiones.ranking_logic import sync_all_users_ranking
from app.misiones.misiones_logic import procesar_misiones_vencidas


def init_scheduler(Session):
    scheduler = BackgroundScheduler()

    # Ranking semanal — domingos a las 23:00
    scheduler.add_job(
        func=sync_all_users_ranking,
        args=[Session],
        trigger='cron',
        day_of_week='sun',
        hour=23,
        minute=0
    )

    # Completar/expirar misiones — todos los días a medianoche
    scheduler.add_job(
        func=procesar_misiones_vencidas,
        args=[Session],
        trigger='cron',
        hour=0,
        minute=0
    )

    scheduler.start()
