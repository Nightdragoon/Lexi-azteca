from sqlalchemy import MetaData, select, desc
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


TASA_MENSUAL = 0.0417  # ~50% anual / 12


def _calcular_pago_mensual(monto, tasa, plazo):
    """Fórmula de amortización francesa."""
    if tasa == 0:
        return round(monto / plazo, 2)
    return round(monto * (tasa * (1 + tasa) ** plazo) / ((1 + tasa) ** plazo - 1), 2)


def solicitar_credito(engine, user_id, monto, plazo_meses):
    meta = MetaData()
    meta.reflect(bind=engine, only=['usuarios', 'simulacion_credito_personal'])
    usuarios_t = meta.tables['usuarios']
    credito_t = meta.tables['simulacion_credito_personal']

    with engine.connect() as conn:
        if not conn.execute(select(usuarios_t).where(usuarios_t.c.user_id == user_id)).fetchone():
            return None, "Usuario no encontrado"

        activo = conn.execute(
            select(credito_t).where(
                credito_t.c.user_id == user_id,
                credito_t.c.estado == 'activo'
            )
        ).fetchone()
        if activo:
            return None, "Ya tienes un crédito personal activo"

        monto = float(monto)
        plazo_meses = int(plazo_meses)
        if monto < 1000 or monto > 50000:
            return None, "El monto debe estar entre $1,000 y $50,000 MXN"
        if plazo_meses not in [6, 12, 24, 36]:
            return None, "Los plazos disponibles son: 6, 12, 24 o 36 meses"

        pago_mensual = _calcular_pago_mensual(monto, TASA_MENSUAL, plazo_meses)
        hoy = date.today()
        fecha_proximo_pago = hoy + relativedelta(months=1)

        row = conn.execute(
            credito_t.insert().values(
                user_id=user_id,
                monto_original=monto,
                tasa_mensual=TASA_MENSUAL,
                plazo_meses=plazo_meses,
                pago_mensual=pago_mensual,
                saldo_pendiente=monto,
                meses_pagados=0,
                fecha_inicio=hoy,
                fecha_proximo_pago=fecha_proximo_pago,
                estado='activo',
            ).returning(*credito_t.columns)
        ).fetchone()
        conn.commit()

    return _formato_credito(row), None


def obtener_credito(engine, user_id):
    meta = MetaData()
    meta.reflect(bind=engine, only=['simulacion_credito_personal'])
    credito_t = meta.tables['simulacion_credito_personal']

    with engine.connect() as conn:
        row = conn.execute(
            select(credito_t).where(
                credito_t.c.user_id == user_id,
                credito_t.c.estado == 'activo'
            )
        ).fetchone()

    if not row:
        return None, "Sin crédito activo"
    return _formato_credito(row), None


def pagar_credito_personal(engine, user_id, monto_pago):
    meta = MetaData()
    meta.reflect(bind=engine, only=[
        'usuarios', 'wallet_state',
        'simulacion_credito_personal', 'pagos_credito_simulado'
    ])
    usuarios_t  = meta.tables['usuarios']
    wallet_t    = meta.tables['wallet_state']
    credito_t   = meta.tables['simulacion_credito_personal']
    pagos_t     = meta.tables['pagos_credito_simulado']

    with engine.connect() as conn:
        if not conn.execute(select(usuarios_t).where(usuarios_t.c.user_id == user_id)).fetchone():
            return None, "Usuario no encontrado"

        credito = conn.execute(
            select(credito_t).where(
                credito_t.c.user_id == user_id,
                credito_t.c.estado == 'activo'
            )
        ).fetchone()
        if not credito:
            return None, "No tienes un crédito personal activo"

        wallet = conn.execute(select(wallet_t).where(wallet_t.c.user_id == user_id)).fetchone()
        if not wallet:
            return None, "No tienes wallet activo"

        monto_pago = float(monto_pago)
        saldo = float(credito.saldo_pendiente)
        cant_rest = float(wallet.cant_rest)

        if monto_pago <= 0:
            return None, "El monto debe ser mayor a cero"
        if monto_pago > saldo:
            monto_pago = saldo  # paga lo que queda
        if monto_pago > cant_rest:
            return None, "Fondos insuficientes en tu wallet"

        # Calcular capital e interés
        interes = round(saldo * float(credito.tasa_mensual), 2)
        capital = round(min(monto_pago - interes, saldo), 2)
        if capital < 0:
            capital = 0
            interes = monto_pago

        nuevo_saldo = round(saldo - capital, 2)
        nuevo_cant_rest = round(cant_rest - monto_pago, 2)
        nuevos_meses = credito.meses_pagados + 1
        nuevo_estado = 'liquidado' if nuevo_saldo <= 0 else 'activo'
        nueva_fecha = date.today() + relativedelta(months=1)

        conn.execute(
            credito_t.update().where(credito_t.c.credito_id == credito.credito_id).values(
                saldo_pendiente=max(nuevo_saldo, 0),
                meses_pagados=nuevos_meses,
                fecha_proximo_pago=nueva_fecha,
                estado=nuevo_estado,
            )
        )
        conn.execute(wallet_t.update().where(wallet_t.c.user_id == user_id).values(cant_rest=nuevo_cant_rest))
        pago_row = conn.execute(
            pagos_t.insert().values(
                credito_id=credito.credito_id,
                user_id=user_id,
                capital_abonado=capital,
                interes_pagado=interes,
                monto_total=monto_pago,
                saldo_despues=max(nuevo_saldo, 0),
            ).returning(*pagos_t.columns)
        ).fetchone()
        conn.commit()

    return {
        "pago_id": pago_row.pago_id,
        "monto_total": monto_pago,
        "capital_abonado": capital,
        "interes_pagado": interes,
        "saldo_despues": max(nuevo_saldo, 0),
        "estado_credito": nuevo_estado,
        "wallet": {"current_budget": nuevo_cant_rest},
    }, None


def tabla_amortizacion(engine, user_id):
    meta = MetaData()
    meta.reflect(bind=engine, only=['simulacion_credito_personal'])
    credito_t = meta.tables['simulacion_credito_personal']

    with engine.connect() as conn:
        credito = conn.execute(
            select(credito_t).where(
                credito_t.c.user_id == user_id,
                credito_t.c.estado == 'activo'
            )
        ).fetchone()
    if not credito:
        return None, "Sin crédito activo"

    tasa = float(credito.tasa_mensual)
    saldo = float(credito.saldo_pendiente)
    pago = float(credito.pago_mensual)
    tabla = []
    fecha = credito.fecha_proximo_pago

    for mes in range(1, credito.plazo_meses - credito.meses_pagados + 1):
        interes = round(saldo * tasa, 2)
        capital = round(pago - interes, 2)
        saldo = round(max(saldo - capital, 0), 2)
        tabla.append({
            "mes": credito.meses_pagados + mes,
            "pago": pago,
            "capital": capital,
            "interes": interes,
            "saldo": saldo,
            "fecha": str(fecha),
        })
        fecha = fecha + relativedelta(months=1)
        if saldo <= 0:
            break

    return {"credito_id": credito.credito_id, "tabla": tabla}, None


def _formato_credito(row):
    return {
        "credito_id": row.credito_id,
        "monto_original": float(row.monto_original),
        "tasa_mensual": float(row.tasa_mensual),
        "tasa_anual_pct": round(float(row.tasa_mensual) * 12 * 100, 1),
        "plazo_meses": row.plazo_meses,
        "pago_mensual": float(row.pago_mensual),
        "saldo_pendiente": float(row.saldo_pendiente),
        "meses_pagados": row.meses_pagados,
        "meses_restantes": row.plazo_meses - row.meses_pagados,
        "fecha_inicio": str(row.fecha_inicio),
        "fecha_proximo_pago": str(row.fecha_proximo_pago),
        "estado": row.estado,
    }
