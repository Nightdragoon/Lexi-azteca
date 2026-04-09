from sqlalchemy import MetaData, select


def obtener_estado(engine, user_id):
    meta = MetaData()
    meta.reflect(bind=engine, only=['usuarios', 'wallet_state'])

    usuarios_table = meta.tables['usuarios']
    wallet_table = meta.tables['wallet_state']

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
            return None, "El usuario no tiene wallet activo. Usa /simulador/wallet/start primero"

    return {
        "user_id": user_id,
        "current_budget": float(wallet.cant_rest),
        "credito_balance": float(wallet.credito_balance) if wallet.credito_balance is not None else 4200.0,
        "monthly_balance": wallet.monthly_balance,
        "max_range": float(wallet.max_range),
        "low_range": float(wallet.low_range),
        "financial_health": float(wallet.financial_health) if wallet.financial_health is not None else 0,
    }, None
