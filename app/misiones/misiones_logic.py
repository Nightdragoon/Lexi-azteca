from datetime import datetime
from sqlalchemy import text

XP_POR_NIVEL = 200


def calcular_nivel(xp_total):
    return (xp_total // XP_POR_NIVEL) + 1


# ── Validadores ───────────────────────────────────────────────────────────────

def _validar_primer_gasto(session, user_id, desde):
    result = session.execute(
        text("SELECT COUNT(*) FROM transacciones WHERE user_id=:uid AND timestamp >= :desde"),
        {"uid": user_id, "desde": desde.strftime("%Y-%m-%d %H:%M:%S")}
    ).scalar()
    return result >= 1, "Registra al menos 1 gasto"


def _validar_categorizar_gastos(session, user_id, desde):
    result = session.execute(
        text("""
            SELECT COUNT(DISTINCT category) FROM transacciones
            WHERE user_id=:uid AND timestamp >= :desde AND category IS NOT NULL
        """),
        {"uid": user_id, "desde": desde.strftime("%Y-%m-%d %H:%M:%S")}
    ).scalar()
    return result >= 3, f"Necesitas 3 categorías distintas, llevas {result}"


def _validar_ahorro_consciente(session, user_id, desde):
    result = session.execute(
        text("""
            SELECT COUNT(*) FROM transacciones
            WHERE user_id=:uid AND category='entretenimiento'
              AND amount < 100 AND timestamp >= :desde
        """),
        {"uid": user_id, "desde": desde.strftime("%Y-%m-%d %H:%M:%S")}
    ).scalar()
    return result >= 1, "Registra un gasto menor a 100 en entretenimiento"


def _validar_reducir_comida(session, user_id, desde):
    wallet = session.execute(
        text("SELECT low_range FROM wallet_state WHERE user_id=:uid"),
        {"uid": user_id}
    ).fetchone()
    if not wallet:
        return False, "Sin wallet activo"
    limite = float(wallet[0]) * 0.30
    total = session.execute(
        text("""
            SELECT COALESCE(SUM(amount), 0) FROM transacciones
            WHERE user_id=:uid AND category='comida' AND timestamp >= :desde
        """),
        {"uid": user_id, "desde": desde.strftime("%Y-%m-%d %H:%M:%S")}
    ).scalar()
    return float(total) <= limite, f"Gastos comida ({total}) superan el 30% del low_range ({limite:.2f})"


def _validar_primera_semana(session, user_id, desde):
    result = session.execute(
        text("SELECT COUNT(*) FROM transacciones WHERE user_id=:uid AND timestamp >= :desde"),
        {"uid": user_id, "desde": desde.strftime("%Y-%m-%d %H:%M:%S")}
    ).scalar()
    return result >= 5, f"Necesitas 5 transacciones, llevas {result}"


VALIDADORES = {
    2: _validar_primer_gasto,
    3: _validar_categorizar_gastos,
    5: _validar_ahorro_consciente,
    7: _validar_reducir_comida,
    8: _validar_primera_semana,
}


# ── Job del scheduler ─────────────────────────────────────────────────────────

def _otorgar_xp(session, user_id, xp_drop):
    existente = session.execute(
        text("SELECT xp FROM user_expirience WHERE user_id=:uid"),
        {"uid": user_id}
    ).fetchone()

    if existente:
        nuevo_xp = existente[0] + xp_drop
        nuevo_nivel = calcular_nivel(nuevo_xp)
        session.execute(
            text("UPDATE user_expirience SET xp=:xp, current_level=:lvl WHERE user_id=:uid"),
            {"xp": nuevo_xp, "lvl": nuevo_nivel, "uid": user_id}
        )
    else:
        nuevo_xp = xp_drop
        nuevo_nivel = calcular_nivel(nuevo_xp)
        session.execute(
            text("INSERT INTO user_expirience (user_id, xp, current_level) VALUES (:uid, :xp, :lvl)"),
            {"uid": user_id, "xp": nuevo_xp, "lvl": nuevo_nivel}
        )


def procesar_misiones_vencidas(Session):
    """
    Job diario a medianoche: revisa misiones activas vencidas,
    valida condiciones y otorga XP o marca como expiradas.
    """
    session = Session()
    try:
        ahora = datetime.now()

        vencidas = session.execute(text("""
            SELECT am.acc_mission_id, am.user_id, am.mision_id, am.time_acc_mission,
                   m.mision_type, m.xp_drop, m.time_limit_days, m.mission_name
            FROM acepted_missions am
            JOIN missiones m ON am.mision_id = m.mission_id
            WHERE am.status = 'activa'
              AND am.time_acc_mission + (m.time_limit_days * INTERVAL '1 day') <= :ahora
        """), {"ahora": ahora}).fetchall()

        completadas = 0
        expiradas = 0

        for row in vencidas:
            acc_id     = row[0]
            user_id    = row[1]
            mision_id  = row[2]
            desde      = row[3]
            tipo       = row[4]
            xp_drop    = row[5]
            nombre     = row[7]

            # Misiones de pregunta: las maneja la IA, se saltan por ahora
            if tipo == 'pregunta':
                continue

            validador = VALIDADORES.get(mision_id)
            if not validador:
                print(f"[misiones] Sin validador para mission_id={mision_id}, se omite")
                continue

            cumplida, msg = validador(session, user_id, desde)

            if cumplida:
                session.execute(
                    text("UPDATE acepted_missions SET status='completada' WHERE acc_mission_id=:id"),
                    {"id": acc_id}
                )
                _otorgar_xp(session, user_id, xp_drop)
                completadas += 1
                print(f"[misiones] ✓ user={user_id} completó '{nombre}' (+{xp_drop} XP)")
            else:
                session.execute(
                    text("UPDATE acepted_missions SET status='expirada' WHERE acc_mission_id=:id"),
                    {"id": acc_id}
                )
                expiradas += 1
                print(f"[misiones] ✗ user={user_id} expiró '{nombre}': {msg}")

        session.commit()
        print(f"[misiones] Proceso diario: {completadas} completadas, {expiradas} expiradas.")

    except Exception as e:
        session.rollback()
        print(f"[misiones] Error en proceso diario: {e}")
    finally:
        session.close()
