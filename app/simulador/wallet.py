from sqlalchemy import MetaData, Table, select




def iniciar_wallet(engine, user_id, max_range, low_range, monthly_balance):
    meta = MetaData()
    meta.reflect(bind=engine, only=['usuarios', 'wallet_state'])

    usuarios_table = meta.tables['usuarios']
    wallet_table = meta.tables['wallet_state']

    with engine.connect() as conn:
        # Verificar que el usuario existe
        usuario = conn.execute(
            select(usuarios_table).where(usuarios_table.c.user_id == user_id)
        ).fetchone()

        if not usuario:
            return None, "Usuario no encontrado"

        # Verificar que no tenga ya un wallet activo
        wallet_existente = conn.execute(
            select(wallet_table).where(wallet_table.c.user_id == user_id)
        ).fetchone()

        if wallet_existente:
            return None, "El usuario ya tiene un wallet activo"

        # Calcular superávit y salud financiera como porcentaje
        monthly_balance_num = float(monthly_balance)
        gastos_estimados = (float(max_range) + float(low_range)) / 2
        superavit = monthly_balance_num - gastos_estimados
        if monthly_balance_num > 0:
            financial_health = round(max(0, min(100, (superavit / monthly_balance_num) * 100)), 2)
        else:
            financial_health = 0

        resultado = conn.execute(
            wallet_table.insert().values(
                user_id=user_id,
                max_range=max_range,
                low_range=low_range,
                cant_rest=round(superavit, 2),
                monthly_balance=str(monthly_balance),
                financial_health=financial_health,
            ).returning(*wallet_table.columns)
        )
        row = resultado.fetchone()
        conn.commit()

    return {k: str(v) if v is not None else None for k, v in row._mapping.items()}, None


#historial de wallet

