from sqlalchemy import MetaData, select
from datetime import datetime


def pagar_credito(engine, user_id, amount):
    meta = MetaData()
    meta.reflect(bind=engine, only=['usuarios', 'wallet_state', 'simulacion_movimientos'])

    usuarios_table = meta.tables['usuarios']
    wallet_table = meta.tables['wallet_state']
    movimientos_table = meta.tables['simulacion_movimientos']

    with engine.connect() as conn:
        usuario = conn.execute(
            select(usuarios_table).where(usuarios_table.c.user_id == user_id)
        ).fetchone()
        if not usuario:
            return None, "Usuario no encontrado"

        wallet = conn.execute(
            select(wallet_table).where(wallet_table.c.user_id == user_id)
        ).fetchone()
        if not wallet:
            return None, "El usuario no tiene wallet activo"

        monto = float(amount)
        if monto <= 0:
            return None, "El monto debe ser mayor a cero"

        credito_balance = float(wallet.credito_balance) if wallet.credito_balance is not None else 0
        cant_rest = float(wallet.cant_rest)

        if credito_balance <= 0:
            return None, "No tienes saldo pendiente en este crédito simulado"
        if monto > credito_balance:
            return None, "El monto supera el saldo pendiente del crédito"
        if monto > cant_rest:
            return None, "Fondos insuficientes en tu cuenta simulada"

        nuevo_budget = round(cant_rest - monto, 2)
        nuevo_credito = round(credito_balance - monto, 2)

        conn.execute(
            wallet_table.update()
            .where(wallet_table.c.user_id == user_id)
            .values(cant_rest=nuevo_budget, credito_balance=nuevo_credito)
        )

        row = conn.execute(
            movimientos_table.insert().values(
                user_id=user_id,
                tipo='pago_credito',
                amount=monto,
                concepto='Crédito personal simulado · aplicación a capital',
                timestamp=datetime.now(),
            ).returning(*movimientos_table.columns)
        ).fetchone()

        conn.commit()

    return {
        "movimiento_id": row.movimiento_id,
        "tipo": "pago_credito",
        "amount": monto,
        "timestamp": row.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        "wallet": {
            "current_budget": nuevo_budget,
            "credito_balance": nuevo_credito,
        }
    }, None
