from flask import Blueprint, jsonify, current_app
from app.misiones.hostorial_transacciones import obtener_historial

historial_bl = Blueprint('historial', __name__, url_prefix='/simulador')


@historial_bl.route('/historial/<int:user_id>', methods=['GET'])
def get_historial(user_id):
    """
    Historial de transacciones del usuario
    ---
    tags:
      - wallet
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: ID del usuario
    responses:
      200:
        description: Lista de transacciones ordenadas de más reciente a más antigua
        schema:
          type: object
          properties:
            user_id:
              type: integer
              example: 1
            total:
              type: integer
              example: 5
            transacciones:
              type: array
              items:
                type: object
                properties:
                  transaction_id:
                    type: integer
                  amount:
                    type: number
                  category:
                    type: string
                  description:
                    type: string
                  timestamp:
                    type: string
                    example: "2026-04-08 14:30:00"
      404:
        description: Usuario no encontrado
    """
    transacciones, error = obtener_historial(
        engine=current_app.engine,
        user_id=user_id,
    )

    if error == "Usuario no encontrado":
        return jsonify({"error": error}), 404

    return jsonify({
        "user_id": user_id,
        "total": len(transacciones),
        "transacciones": transacciones,
    }), 200
