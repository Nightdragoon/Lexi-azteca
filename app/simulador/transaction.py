from sqlalchemy import MetaData, select
from datetime import datetime


def registrar_transaccion(engine, user_id, amount, category, description):
    meta = MetaData()
    meta.reflect(bind=engine, only=['usuarios', 'wallet_state', 'transacciones'])

    usuarios_table = meta.tables['usuarios']
    wallet_table = meta.tables['wallet_state']
    transacciones_table = meta.tables['transacciones']

    with engine.connect() as conn:
        # Verificar que el usuario existe
        usuario = conn.execute(
            select(usuarios_table).where(usuarios_table.c.user_id == user_id)
        ).fetchone()
        if not usuario:
            return None, "Usuario no encontrado"

        # Verificar que tiene wallet activo
        wallet = conn.execute(
            select(wallet_table).where(wallet_table.c.user_id == user_id)
        ).fetchone()
        if not wallet:
            return None, "El usuario no tiene un wallet activo. Usa /simulador/wallet/start primero"

        # Insertar transacción
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_tx = conn.execute(
            transacciones_table.insert().values(
                user_id=user_id,
                amount=amount,
                category=category,
                description=description,
                timestamp=timestamp,
            ).returning(*transacciones_table.columns)
        ).fetchone()

        # Actualizar cant_rest y recalcular financial_health
        nuevo_cant_rest = float(wallet.cant_rest) - float(amount)
        nuevo_health = nuevo_cant_rest >= float(wallet.low_range)

        conn.execute(
            wallet_table.update()
            .where(wallet_table.c.user_id == user_id)
            .values(cant_rest=round(nuevo_cant_rest, 2), financial_health=nuevo_health)
        )
        conn.commit()

    return {
        "transaccion": {k: str(v) if v is not None else None for k, v in row_tx._mapping.items()},
        "wallet": {
            "cant_rest": round(nuevo_cant_rest, 2),
            "financial_health": nuevo_health,
        }
    }, None
