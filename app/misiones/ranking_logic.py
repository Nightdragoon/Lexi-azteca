from datetime import datetime, timedelta
from sqlalchemy import text


def get_week_start():
    today = datetime.utcnow()
    start = today - timedelta(days=today.weekday())
    return start.replace(hour=0, minute=0, second=0, microsecond=0)


def update_user_ranking(session, user_id):
    """
    Actualiza o crea el registro de week_ranking del usuario para la semana actual.
    xp_diference = XP total actual - XP al inicio de la semana (snapshot de semana anterior)
    """
    week_start = get_week_start()
    last_week_start = week_start - timedelta(days=7)

    # XP actual del usuario
    user_xp = session.execute(
        text("SELECT xp FROM user_expirience WHERE user_id = :user_id"),
        {"user_id": user_id}
    ).fetchone()

    if not user_xp:
        return None

    current_xp = user_xp[0] or 0

    # XP de la semana pasada (snapshot)
    last_week_record = session.execute(
        text("""
            SELECT xp_diference FROM week_ranking
            WHERE user_id = :user_id
              AND week >= :last_week_start
              AND week < :week_start
            ORDER BY week DESC
            LIMIT 1
        """),
        {"user_id": user_id, "last_week_start": last_week_start, "week_start": week_start}
    ).fetchone()

    xp_last_week = last_week_record[0] if last_week_record else 0
    xp_diff = max(current_xp - xp_last_week, 0)

    # Verificar si ya existe registro esta semana
    existing = session.execute(
        text("""
            SELECT rank_id FROM week_ranking
            WHERE user_id = :user_id AND week >= :week_start
        """),
        {"user_id": user_id, "week_start": week_start}
    ).fetchone()

    if existing:
        session.execute(
            text("""
                UPDATE week_ranking
                SET xp_diference = :xp_diff
                WHERE rank_id = :rank_id
            """),
            {"xp_diff": xp_diff, "rank_id": existing[0]}
        )
    else:
        session.execute(
            text("""
                INSERT INTO week_ranking (user_id, week, xp_diference)
                VALUES (:user_id, :week_start, :xp_diff)
            """),
            {"user_id": user_id, "week_start": week_start, "xp_diff": xp_diff}
        )

    session.commit()


def sync_all_users_ranking(Session):
    """
    Job semanal: actualiza xp_diference de todos los usuarios.
    Corre automaticamente cada domingo a las 23:00.
    """
    session = Session()
    try:
        usuarios = session.execute(
            text("SELECT user_id FROM user_expirience")
        ).fetchall()

        for row in usuarios:
            update_user_ranking(session, row[0])

        print(f"[ranking] Sync semanal completado para {len(usuarios)} usuarios.")
    except Exception as e:
        session.rollback()
        print(f"[ranking] Error en sync semanal: {e}")
    finally:
        session.close()


def get_ranking(session, user_id):
    """
    Retorna el top 10 de la semana actual y la posicion del usuario.
    """
    week_start = get_week_start()

    # Top 10 de la semana
    top_10 = session.execute(
        text("""
            SELECT wr.user_id, u.user_name, wr.xp_diference,
                   ROW_NUMBER() OVER (ORDER BY wr.xp_diference DESC) AS position
            FROM week_ranking wr
            JOIN usuarios u ON wr.user_id = u.user_id
            WHERE wr.week >= :week_start
            ORDER BY wr.xp_diference DESC
            LIMIT 10
        """),
        {"week_start": week_start}
    ).fetchall()

    # Posicion del usuario
    user_position = session.execute(
        text("""
            SELECT COUNT(*) + 1
            FROM week_ranking
            WHERE week >= :week_start
              AND xp_diference > COALESCE(
                (SELECT xp_diference FROM week_ranking
                 WHERE user_id = :user_id AND week >= :week_start
                 LIMIT 1), 0
              )
        """),
        {"week_start": week_start, "user_id": user_id}
    ).scalar()

    return {
        "semana": week_start.strftime("%Y-%m-%d"),
        "top_10": [
            {
                "posicion": row[3],
                "user_id": row[0],
                "user_name": row[1],
                "xp_semana": row[2]
            }
            for row in top_10
        ],
        "tu_posicion": user_position or 0
    }
