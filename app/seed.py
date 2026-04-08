from sqlalchemy import MetaData, Table, select

USUARIOS_SEED = [
    {"user_name": "test_user1", "user_phone": "5210000000001", "password": "test123", "onboarding": False},
    {"user_name": "test_user2", "user_phone": "5210000000002", "password": "test123", "onboarding": False},
    {"user_name": "test_user3", "user_phone": "5210000000003", "password": "test123", "onboarding": False},
]


def seed_usuarios(engine):
    meta = MetaData()
    meta.reflect(bind=engine, only=['usuarios'])
    tabla = meta.tables['usuarios']

    with engine.connect() as conn:
        count = conn.execute(select(tabla)).fetchall()
        if len(count) >= 3:
            print(f"[seed] Ya existen {len(count)} usuarios, no se insertan datos.")
            return

        existentes = {row.user_name for row in count}
        insertados = 0
        for usuario in USUARIOS_SEED:
            if usuario['user_name'] not in existentes:
                conn.execute(tabla.insert().values(**usuario))
                insertados += 1

        conn.commit()
        print(f"[seed] {insertados} usuario(s) de prueba insertados.")
