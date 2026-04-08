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


#lista de misiones
