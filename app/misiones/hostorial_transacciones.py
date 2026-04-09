from sqlalchemy import MetaData, Table, select, desc


def obtener_historial(engine, user_id):
    meta = MetaData()
    meta.reflect(bind=engine, only=['usuarios', 'transacciones'])

    usuarios_table = meta.tables['usuarios']
    transacciones_table = meta.tables['transacciones']

    with engine.connect() as conn:
        usuario = conn.execute(
            select(usuarios_table).where(usuarios_table.c.user_id == user_id)
        ).fetchone()

        if not usuario:
            return None, "Usuario no encontrado"

        rows = conn.execute(
            select(transacciones_table)
            .where(transacciones_table.c.user_id == user_id)
            .order_by(desc(transacciones_table.c.timestamp))
        ).fetchall()

    transacciones = []
    for row in rows:
        data = dict(row._mapping)
        if data.get('timestamp') is not None:
            data['timestamp'] = data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        data['amount'] = float(data['amount']) if data['amount'] is not None else None
        transacciones.append(data)

    return transacciones, None
