from sqlalchemy import MetaData, select, desc
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import calendar


TASA_MENSUAL_TARJETA = 0.05     # 60% anual / 12
PAGO_MINIMO_PCT = 0.10          # 10% del saldo
PAGO_MINIMO_FIJO = 500.0        # mínimo absoluto en MXN
DIAS_GRACIA = 20                # días después del corte para pagar


def _calcular_proxima_fecha_corte(dia_corte):
    hoy = date.today()
    if hoy.day < dia_corte:
        try:
            return hoy.replace(day=dia_corte)
        except ValueError:
            ultimo = calendar.monthrange(hoy.year, hoy.month)[1]
            return hoy.replace(day=ultimo)
    else:
        siguiente = hoy + relativedelta(months=1)
        try:
            return siguiente.replace(day=dia_corte)
        except ValueError:
            ultimo = calendar.monthrange(siguiente.year, siguiente.month)[1]
            return siguiente.replace(day=ultimo)


def activar_tarjeta(engine, user_id, limite_credito, dia_corte=15):
    meta = MetaData()
    meta.reflect(bind=engine, only=['usuarios', 'simulacion_tarjeta_credito'])
    usuarios_t = meta.tables['usuarios']
    tarjeta_t  = meta.tables['simulacion_tarjeta_credito']

    with engine.connect() as conn:
        if not conn.execute(select(usuarios_t).where(usuarios_t.c.user_id == user_id)).fetchone():
            return None, "Usuario no encontrado"

        activa = conn.execute(
            select(tarjeta_t).where(
                tarjeta_t.c.user_id == user_id,
                tarjeta_t.c.estado == 'activa'
            )
        ).fetchone()
        if activa:
            return None, "Ya tienes una tarjeta de crédito activa"

        limite = float(limite_credito)
        if limite < 1000 or limite > 20000:
            return None, "El límite debe estar entre $1,000 y $20,000 MXN"
        if dia_corte < 1 or dia_corte > 28:
            return None, "El día de corte debe estar entre 1 y 28"

        fecha_corte       = _calcular_proxima_fecha_corte(dia_corte)
        fecha_limite_pago = fecha_corte + relativedelta(days=DIAS_GRACIA)

        row = conn.execute(
            tarjeta_t.insert().values(
                user_id=user_id,
                limite_credito=limite,
                saldo_utilizado=0,
                dia_corte=dia_corte,
                fecha_corte=fecha_corte,
                fecha_limite_pago=fecha_limite_pago,
                pago_minimo=0,
                estado='activa',
            ).returning(*tarjeta_t.columns)
        ).fetchone()
        conn.commit()

    return _formato_tarjeta(row), None


def obtener_tarjeta(engine, user_id):
    meta = MetaData()
    meta.reflect(bind=engine, only=['simulacion_tarjeta_credito'])
    tarjeta_t = meta.tables['simulacion_tarjeta_credito']

    with engine.connect() as conn:
        row = conn.execute(
            select(tarjeta_t).where(
                tarjeta_t.c.user_id == user_id,
                tarjeta_t.c.estado == 'activa'
            )
        ).fetchone()

    if not row:
        return None, "Sin tarjeta activa"
    return _formato_tarjeta(row), None


def hacer_cargo(engine, user_id, monto, descripcion=""):
    meta = MetaData()
    meta.reflect(bind=engine, only=['usuarios', 'simulacion_tarjeta_credito', 'movimientos_tarjeta'])
    usuarios_t = meta.tables['usuarios']
    tarjeta_t  = meta.tables['simulacion_tarjeta_credito']
    movs_t     = meta.tables['movimientos_tarjeta']

    with engine.connect() as conn:
        if not conn.execute(select(usuarios_t).where(usuarios_t.c.user_id == user_id)).fetchone():
            return None, "Usuario no encontrado"

        tarjeta = conn.execute(
            select(tarjeta_t).where(
                tarjeta_t.c.user_id == user_id,
                tarjeta_t.c.estado == 'activa'
            )
        ).fetchone()
        if not tarjeta:
            return None, "No tienes tarjeta de crédito activa"

        monto = float(monto)
        disponible = float(tarjeta.limite_credito) - float(tarjeta.saldo_utilizado)
        if monto <= 0:
            return None, "El monto debe ser mayor a cero"
        if monto > disponible:
            return None, f"Crédito insuficiente. Disponible: ${disponible:,.2f}"

        nuevo_saldo = round(float(tarjeta.saldo_utilizado) + monto, 2)
        nuevo_minimo = max(round(nuevo_saldo * PAGO_MINIMO_PCT, 2), PAGO_MINIMO_FIJO if nuevo_saldo > 0 else 0)

        conn.execute(
            tarjeta_t.update().where(tarjeta_t.c.tarjeta_id == tarjeta.tarjeta_id).values(
                saldo_utilizado=nuevo_saldo,
                pago_minimo=nuevo_minimo,
            )
        )
        mov = conn.execute(
            movs_t.insert().values(
                tarjeta_id=tarjeta.tarjeta_id,
                user_id=user_id,
                tipo='cargo',
                monto=monto,
                descripcion=descripcion,
            ).returning(*movs_t.columns)
        ).fetchone()
        conn.commit()

    return {
        "movimiento_id": mov.movimiento_id,
        "tipo": "cargo",
        "monto": monto,
        "descripcion": descripcion,
        "saldo_utilizado": nuevo_saldo,
        "credito_disponible": round(float(tarjeta.limite_credito) - nuevo_saldo, 2),
        "pago_minimo": nuevo_minimo,
    }, None


def pagar_tarjeta(engine, user_id, monto_pago):
    meta = MetaData()
    meta.reflect(bind=engine, only=[
        'usuarios', 'wallet_state',
        'simulacion_tarjeta_credito', 'movimientos_tarjeta'
    ])
    usuarios_t = meta.tables['usuarios']
    wallet_t   = meta.tables['wallet_state']
    tarjeta_t  = meta.tables['simulacion_tarjeta_credito']
    movs_t     = meta.tables['movimientos_tarjeta']

    with engine.connect() as conn:
        if not conn.execute(select(usuarios_t).where(usuarios_t.c.user_id == user_id)).fetchone():
            return None, "Usuario no encontrado"

        tarjeta = conn.execute(
            select(tarjeta_t).where(
                tarjeta_t.c.user_id == user_id,
                tarjeta_t.c.estado == 'activa'
            )
        ).fetchone()
        if not tarjeta:
            return None, "No tienes tarjeta activa"

        wallet = conn.execute(select(wallet_t).where(wallet_t.c.user_id == user_id)).fetchone()
        if not wallet:
            return None, "No tienes wallet activo"

        monto_pago = float(monto_pago)
        saldo_usado = float(tarjeta.saldo_utilizado)
        cant_rest = float(wallet.cant_rest)

        if monto_pago <= 0:
            return None, "El monto debe ser mayor a cero"
        if saldo_usado <= 0:
            return None, "No tienes saldo pendiente en tu tarjeta"
        if monto_pago > saldo_usado:
            monto_pago = saldo_usado
        if monto_pago > cant_rest:
            return None, "Fondos insuficientes en tu wallet"

        nuevo_saldo_tarjeta = round(saldo_usado - monto_pago, 2)
        nuevo_minimo = max(round(nuevo_saldo_tarjeta * PAGO_MINIMO_PCT, 2), PAGO_MINIMO_FIJO) if nuevo_saldo_tarjeta > 0 else 0
        nuevo_cant_rest = round(cant_rest - monto_pago, 2)

        # Recalcular siguiente fecha de corte
        fecha_corte       = _calcular_proxima_fecha_corte(tarjeta.dia_corte)
        fecha_limite_pago = fecha_corte + relativedelta(days=DIAS_GRACIA)

        conn.execute(
            tarjeta_t.update().where(tarjeta_t.c.tarjeta_id == tarjeta.tarjeta_id).values(
                saldo_utilizado=nuevo_saldo_tarjeta,
                pago_minimo=nuevo_minimo,
                fecha_corte=fecha_corte,
                fecha_limite_pago=fecha_limite_pago,
            )
        )
        conn.execute(wallet_t.update().where(wallet_t.c.user_id == user_id).values(cant_rest=nuevo_cant_rest))
        mov = conn.execute(
            movs_t.insert().values(
                tarjeta_id=tarjeta.tarjeta_id,
                user_id=user_id,
                tipo='pago',
                monto=monto_pago,
                descripcion='Pago a tarjeta de crédito',
            ).returning(*movs_t.columns)
        ).fetchone()
        conn.commit()

    return {
        "movimiento_id": mov.movimiento_id,
        "tipo": "pago",
        "monto_pagado": monto_pago,
        "saldo_restante": nuevo_saldo_tarjeta,
        "pago_minimo_nuevo": nuevo_minimo,
        "fecha_corte": str(fecha_corte),
        "fecha_limite_pago": str(fecha_limite_pago),
        "wallet": {"current_budget": nuevo_cant_rest},
    }, None


def movimientos_tarjeta(engine, user_id):
    meta = MetaData()
    meta.reflect(bind=engine, only=['simulacion_tarjeta_credito', 'movimientos_tarjeta'])
    tarjeta_t = meta.tables['simulacion_tarjeta_credito']
    movs_t    = meta.tables['movimientos_tarjeta']

    with engine.connect() as conn:
        tarjeta = conn.execute(
            select(tarjeta_t).where(
                tarjeta_t.c.user_id == user_id,
                tarjeta_t.c.estado == 'activa'
            )
        ).fetchone()
        if not tarjeta:
            return None, "Sin tarjeta activa"

        rows = conn.execute(
            select(movs_t)
            .where(movs_t.c.tarjeta_id == tarjeta.tarjeta_id)
            .order_by(desc(movs_t.c.timestamp))
        ).fetchall()

    movs = []
    for r in rows:
        d = dict(r._mapping)
        if d.get('timestamp'):
            d['timestamp'] = d['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        d['monto'] = float(d['monto'])
        movs.append(d)

    return {"tarjeta_id": tarjeta.tarjeta_id, "movimientos": movs}, None


def _formato_tarjeta(row):
    saldo = float(row.saldo_utilizado)
    limite = float(row.limite_credito)
    return {
        "tarjeta_id": row.tarjeta_id,
        "limite_credito": limite,
        "saldo_utilizado": saldo,
        "credito_disponible": round(limite - saldo, 2),
        "uso_pct": round((saldo / limite) * 100, 1) if limite > 0 else 0,
        "dia_corte": row.dia_corte,
        "fecha_corte": str(row.fecha_corte),
        "fecha_limite_pago": str(row.fecha_limite_pago),
        "pago_minimo": float(row.pago_minimo),
        "estado": row.estado,
    }
