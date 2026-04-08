from flask import Blueprint, jsonify, current_app
from app.misiones.ranking_logic import update_user_ranking, get_ranking

rk_bp = Blueprint('ranking', __name__, url_prefix='/ranking')


@rk_bp.route('/<int:user_id>', methods=['GET'])
def get_user_ranking(user_id):
    """
    Obtiene el ranking semanal y la posicion del usuario.
    ---
    tags:
      - ranking
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID del usuario
    responses:
      200:
        description: Top 10 del ranking semanal y posicion del usuario
        schema:
          type: object
          properties:
            semana:
              type: string
              example: "2026-04-06"
            top_10:
              type: array
              items:
                type: object
                properties:
                  posicion:
                    type: integer
                  user_id:
                    type: integer
                  user_name:
                    type: string
                  xp_semana:
                    type: integer
            tu_posicion:
              type: integer
      404:
        description: Usuario sin XP registrado
      500:
        description: Error interno
    """
    session = current_app.Session()
    try:
        resultado = update_user_ranking(session, user_id)
        if resultado is None:
            return jsonify({"message": "Sin clasificación"}), 404

        ranking = get_ranking(session, user_id)
        return jsonify(ranking), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()
