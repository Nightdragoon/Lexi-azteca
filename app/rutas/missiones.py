from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.ext.automap import automap_base

ms_bl = Blueprint('misiones', __name__, url_prefix='/misiones')


def get_missions_class():
    Base = automap_base()
    Base.prepare(current_app.engine, reflect=True)
    return Base.classes.missiones


@ms_bl.route('/', methods=['POST'])
def agregar_misiones():
    """
    Agregar misiones
    ---
    tags:
      - misiones
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - mission_name
            - mision_type
            - description
            - status
            - xp_drop
          properties:
            mission_name:
              type: string
              example: "Primera misión"
            mision_type:
              type: string
              enum: [pregunta, completar]
              example: "pregunta"
            description:
              type: string
              example: "Completa el tutorial"
            status:
              type: string
              example: "active"
            xp_drop:
              type: integer
              example: 100
    responses:
      201:
        description: Misión creada
      400:
        description: Error en datos
    """
    session = current_app.Session()
    try:
        Missions = get_missions_class()
        data = request.get_json()
        data.pop('mission_id', None)
        data.pop('created_at', None)
        nuevo = Missions(**data)
        session.add(nuevo)
        session.commit()
        result = {
            col.key: str(getattr(nuevo, col.key)) if getattr(nuevo, col.key) is not None else None
            for col in Missions.__table__.columns
        }
        return jsonify(result), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@ms_bl.route('/', methods=['GET'])
def listar_misiones():
    """
    Listar misiones disponibles
    ---
    tags:
      - misiones
    responses:
      200:
        description: Lista de misiones con status disponible
      400:
        description: Error al obtener misiones
    """
    from sqlalchemy import MetaData, select
    meta = MetaData()
    meta.reflect(bind=current_app.engine, only=['missiones'])
    tabla = meta.tables['missiones']

    with current_app.engine.connect() as conn:
        rows = conn.execute(
            select(tabla).where(tabla.c.status == 'disponible')
        ).fetchall()

    return jsonify([
        {k: str(v) if v is not None else None for k, v in row._mapping.items()}
        for row in rows
    ]), 200


@ms_bl.route('/aceptar', methods=['POST'])
def aceptar_mision():
    """
    Aceptar una misión
    ---
    tags:
      - misiones
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - mision_id
          properties:
            user_id:
              type: integer
              example: 1
            mision_id:
              type: integer
              example: 3
    responses:
      201:
        description: Misión aceptada
      400:
        description: El usuario ya tiene 5 misiones activas o ya aceptó esta misión
      404:
        description: Usuario o misión no encontrada
    """
    from sqlalchemy import MetaData, select, func
    from datetime import datetime

    data = request.get_json()
    user_id = data.get('user_id')
    mision_id = data.get('mision_id')

    meta = MetaData()
    meta.reflect(bind=current_app.engine, only=['usuarios', 'missiones', 'acepted_missions'])

    usuarios_table = meta.tables['usuarios']
    missiones_table = meta.tables['missiones']
    acepted_table = meta.tables['acepted_missions']

    with current_app.engine.connect() as conn:
        # Verificar usuario
        usuario = conn.execute(
            select(usuarios_table).where(usuarios_table.c.user_id == user_id)
        ).fetchone()
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        # Verificar que la misión existe y está disponible
        mision = conn.execute(
            select(missiones_table).where(
                missiones_table.c.mission_id == mision_id,
                missiones_table.c.status == 'disponible'
            )
        ).fetchone()
        if not mision:
            return jsonify({"error": "Misión no encontrada o no disponible"}), 404

        # Verificar que no haya aceptado ya esta misión
        ya_aceptada = conn.execute(
            select(acepted_table).where(
                acepted_table.c.user_id == user_id,
                acepted_table.c.mision_id == mision_id,
            )
        ).fetchone()
        if ya_aceptada:
            return jsonify({"error": "Ya aceptaste esta misión"}), 400

        # Verificar límite de 5 misiones activas
        total = conn.execute(
            select(func.count()).select_from(acepted_table).where(
                acepted_table.c.user_id == user_id
            )
        ).scalar()
        if total >= 5:
            return jsonify({"error": "No puedes tener más de 5 misiones activas a la vez"}), 400

        # Insertar
        row = conn.execute(
            acepted_table.insert().values(
                user_id=user_id,
                mision_id=mision_id,
                time_acc_mission=datetime.now(),
            ).returning(*acepted_table.columns)
        ).fetchone()
        conn.commit()

    return jsonify({k: str(v) if v is not None else None for k, v in row._mapping.items()}), 201


@ms_bl.route('/activas/<int:user_id>', methods=['GET'])
def listar_misiones_activas(user_id):
    """
    Listar misiones activas del usuario
    ---
    tags:
      - misiones
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200:
        description: Lista de misiones aceptadas con su estado
      404:
        description: Usuario no encontrado
    """
    from sqlalchemy import MetaData, select

    meta = MetaData()
    meta.reflect(bind=current_app.engine, only=['acepted_missions', 'missiones'])
    acepted = meta.tables['acepted_missions']
    missiones_t = meta.tables['missiones']

    with current_app.engine.connect() as conn:
        rows = conn.execute(
            select(
                acepted.c.acc_mission_id,
                acepted.c.status,
                acepted.c.time_acc_mission,
                missiones_t.c.mission_name,
                missiones_t.c.mision_type,
                missiones_t.c.description,
                missiones_t.c.xp_drop,
                missiones_t.c.time_limit_days,
            ).join(missiones_t, acepted.c.mision_id == missiones_t.c.mission_id)
            .where(acepted.c.user_id == user_id)
        ).fetchall()

    return jsonify([
        {k: str(v) if v is not None else None for k, v in row._mapping.items()}
        for row in rows
    ]), 200


