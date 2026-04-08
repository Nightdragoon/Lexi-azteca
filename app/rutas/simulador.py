from flask import Blueprint, request, jsonify, current_app
from app.simulador.wallet import iniciar_wallet
from app.simulador.transaction import registrar_transaccion

sim_bl = Blueprint('simulador', __name__, url_prefix='/simulador')


@sim_bl.route('/wallet/start', methods=['POST'])
def wallet_start():
    """
    Iniciar wallet del usuario
    ---
    tags:
      - wallet
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - max_range
            - low_range
            - monthly_balance
          properties:
            user_id:
              type: integer
              example: 1
            max_range:
              type: number
              example: 5000.00
              description: Estimado máximo de gastos mensuales
            low_range:
              type: number
              example: 2000.00
              description: Estimado mínimo de gastos mensuales
            monthly_balance:
              type: string
              example: "8000"
              description: Ingreso mensual del usuario
    responses:
      201:
        description: Wallet iniciado. cant_rest y financial_health calculados automáticamente por superávit.
      400:
        description: Error en datos o usuario ya tiene wallet activo
      404:
        description: Usuario no encontrado
    """
    data = request.get_json()
    resultado, error = iniciar_wallet(
        engine=current_app.engine,
        user_id=data.get('user_id'),
        max_range=data.get('max_range'),
        low_range=data.get('low_range'),
        monthly_balance=data.get('monthly_balance'),
    )
    if error == "Usuario no encontrado":
        return jsonify({"error": error}), 404
    if error:
        return jsonify({"error": error}), 400
    return jsonify(resultado), 201


@sim_bl.route('/wallet/<int:user_id>', methods=['GET'])
def get_wallet(user_id):
    """
    Obtener información del wallet del usuario
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
        description: Información del wallet
      404:
        description: Wallet no encontrado
    """
    from sqlalchemy import MetaData, select
    meta = MetaData()
    meta.reflect(bind=current_app.engine, only=['wallet_state'])
    wallet_table = meta.tables['wallet_state']

    with current_app.engine.connect() as conn:
        row = conn.execute(
            select(wallet_table).where(wallet_table.c.user_id == user_id)
        ).fetchone()

    if not row:
        return jsonify({"error": "Wallet no encontrado para este usuario"}), 404

    return jsonify({k: str(v) if v is not None else None for k, v in row._mapping.items()}), 200


@sim_bl.route('/transaccion', methods=['POST'])
def crear_transaccion():
    """
    Registrar una transacción del usuario
    ---
    tags:
      - wallet
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - amount
          properties:
            user_id:
              type: integer
              example: 1
            amount:
              type: number
              example: 350.00
              description: Monto del gasto
            category:
              type: string
              example: "comida"
              description: Categoría del gasto
            description:
              type: string
              example: "Almuerzo en restaurante"
    responses:
      201:
        description: Transacción registrada y wallet actualizado
      400:
        description: Error en datos o wallet no activo
      404:
        description: Usuario no encontrado
    """
    data = request.get_json()
    resultado, error = registrar_transaccion(
        engine=current_app.engine,
        user_id=data.get('user_id'),
        amount=data.get('amount'),
        category=data.get('category'),
        description=data.get('description'),
    )
    if error == "Usuario no encontrado":
        return jsonify({"error": error}), 404
    if error:
        return jsonify({"error": error}), 400
    return jsonify(resultado), 201
