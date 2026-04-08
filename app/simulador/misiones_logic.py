from sqlalchemy import MetaData, select, func
from datetime import datetime

XP_POR_NIVEL = 200


def calcular_nivel(xp_total):
    return (xp_total // XP_POR_NIVEL) + 1


# ── Validadores por mission_id ────────────────────────────────────────────────
# Cada función recibe (conn, user_id, time_acc_mission) y retorna (bool, str)

def _validar_primer_gasto(conn, tablas, user_id, desde):
    tx = tablas['transacciones']
    count = conn.execute(
        select(func.count()).select_from(tx).where(
            tx.c.user_id == user_id,
            tx.c.timestamp >= desde.strftime("%Y-%m-%d %H:%M:%S"),
        )
    ).scalar()
    if count >= 1:
        return True, "OK"
    return False, "Aún no has registrado ningún gasto desde que aceptaste la misión"


def _validar_categorizar_gastos(conn, tablas, user_id, desde):
    tx = tablas['transacciones']
    rows = conn.execute(
        select(tx.c.category).where(
            tx.c.user_id == user_id,
            tx.c.timestamp >= desde.strftime("%Y-%m-%d %H:%M:%S"),
            tx.c.category.isnot(None),
        )
    ).fetchall()
    categorias = {r.category for r in rows}
    if len(categorias) >= 3:
        return True, "OK"
    return False, f"Necesitas gastos en al menos 3 categorías distintas. Llevas: {len(categorias)}"


def _validar_ahorro_consciente(conn, tablas, user_id, desde):
    tx = tablas['transacciones']
    row = conn.execute(
        select(tx).where(
            tx.c.user_id == user_id,
            tx.c.category == 'entretenimiento',
            tx.c.amount < 100,
            tx.c.timestamp >= desde.strftime("%Y-%m-%d %H:%M:%S"),
        )
    ).fetchone()
    if row:
        return True, "OK"
    return False, "Registra un gasto menor a 100 en la categoría 'entretenimiento'"


def _validar_reducir_comida(conn, tablas, user_id, desde):
    tx = tablas['transacciones']
    ws = tablas['wallet_state']
    wallet = conn.execute(
        select(ws).where(ws.c.user_id == user_id)
    ).fetchone()
    if not wallet:
        return False, "No tienes wallet activo"
    limite = float(wallet.low_range) * 0.30
    total_comida = conn.execute(
        select(func.coalesce(func.sum(tx.c.amount), 0)).where(
            tx.c.user_id == user_id,
            tx.c.category == 'comida',
            tx.c.timestamp >= desde.strftime("%Y-%m-%d %H:%M:%S"),
        )
    ).scalar()
    if float(total_comida) <= limite:
        return True, "OK"
    return False, f"Tus gastos de comida ({total_comida}) superan el 30% de tu low_range ({limite:.2f})"


def _validar_primera_semana(conn, tablas, user_id, desde):
    tx = tablas['transacciones']
    count = conn.execute(
        select(func.count()).select_from(tx).where(
            tx.c.user_id == user_id,
            tx.c.timestamp >= desde.strftime("%Y-%m-%d %H:%M:%S"),
        )
    ).scalar()
    if count >= 5:
        return True, "OK"
    return False, f"Necesitas al menos 5 transacciones. Llevas: {count}"


VALIDADORES = {
    2: _validar_primer_gasto,
    3: _validar_categorizar_gastos,
    5: _validar_ahorro_consciente,
    7: _validar_reducir_comida,
    8: _validar_primera_semana,
}


# ── Función principal ─────────────────────────────────────────────────────────

def completar_mision(engine, user_id, acc_mission_id):
    meta = MetaData()
    meta.reflect(bind=engine, only=[
        'acepted_missions', 'missiones', 'user_expirience', 'transacciones', 'wallet_state'
    ])
    tablas = meta.tables

    acepted = tablas['acepted_missions']
    missiones = tablas['missiones']
    experiencia = tablas['user_expirience']

    with engine.connect() as conn:
        # Buscar la misión aceptada
        acc = conn.execute(
            select(acepted).where(
                acepted.c.acc_mission_id == acc_mission_id,
                acepted.c.user_id == user_id,
            )
        ).fetchone()
        if not acc:
            return None, "Misión aceptada no encontrada"
        if acc.status != 'activa':
            return None, f"Esta misión ya está en estado '{acc.status}'"

        # Buscar los datos de la misión
        mision = conn.execute(
            select(missiones).where(missiones.c.mission_id == acc.mision_id)
        ).fetchone()

        # Verificar si expiró
        dias_limite = mision.time_limit_days or 7
        ahora = datetime.now()
        tiempo_aceptada = acc.time_acc_mission
        dias_transcurridos = (ahora - tiempo_aceptada).days
        if dias_transcurridos > dias_limite:
            conn.execute(
                acepted.update()
                .where(acepted.c.acc_mission_id == acc_mission_id)
                .values(status='expirada')
            )
            conn.commit()
            return None, f"La misión expiró después de {dias_limite} días"

        # Misiones tipo pregunta: pendiente de IA
        if mision.mision_type == 'pregunta':
            return None, "Las misiones de tipo pregunta estarán disponibles próximamente"

        # Validar condiciones de la misión
        validador = VALIDADORES.get(mision.mission_id)
        if not validador:
            return None, "Esta misión no tiene validador configurado aún"

        cumplida, mensaje = validador(conn, tablas, user_id, tiempo_aceptada)
        if not cumplida:
            return None, mensaje

        # Marcar misión como completada
        conn.execute(
            acepted.update()
            .where(acepted.c.acc_mission_id == acc_mission_id)
            .values(status='completada')
        )

        # Otorgar XP
        exp_row = conn.execute(
            select(experiencia).where(experiencia.c.user_id == user_id)
        ).fetchone()

        if exp_row:
            nuevo_xp = exp_row.xp + mision.xp_drop
            nuevo_nivel = calcular_nivel(nuevo_xp)
            conn.execute(
                experiencia.update()
                .where(experiencia.c.user_id == user_id)
                .values(xp=nuevo_xp, current_level=nuevo_nivel)
            )
        else:
            nuevo_xp = mision.xp_drop
            nuevo_nivel = calcular_nivel(nuevo_xp)
            conn.execute(
                experiencia.insert().values(
                    user_id=user_id,
                    xp=nuevo_xp,
                    current_level=nuevo_nivel,
                )
            )

        conn.commit()

    return {
        "mensaje": f"¡Misión '{mision.mission_name}' completada!",
        "xp_ganado": mision.xp_drop,
        "xp_total": nuevo_xp,
        "nivel": nuevo_nivel,
    }, None
