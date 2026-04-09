from flask import Blueprint, request, jsonify, current_app
from app.simulador.estado import obtener_estado
from app.simulador.transferencia import registrar_transferencia
from app.simulador.credito import pagar_credito
from sqlalchemy import MetaData, select, desc

banco_bl = Blueprint('banco', __name__, url_prefix='/simulador')


@banco_bl.route('/estado/<int:user_id>', methods=['GET'])
def get_estado(user_id):
    """
    Estado completo del simulador para el usuario
    ---
    tags:
      - wallet
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200:
        description: Estado del simulador (budget + crédito)
        schema:
          type: object
          properties:
            user_id:
              type: integer
            current_budget:
              type: number
              description: Saldo disponible (cant_rest)
            credito_balance:
              type: number
              description: Saldo pendiente del crédito simulado
            monthly_balance:
              type: string
            max_range:
              type: number
            low_range:
              type: number
            financial_health:
              type: number
      404:
        description: Usuario o wallet no encontrado
    """
    estado, error = obtener_estado(engine=current_app.engine, user_id=user_id)
    if error == "Usuario no encontrado":
        return jsonify({"error": error}), 404
    if error:
        return jsonify({"error": error}), 400
    return jsonify(estado), 200


@banco_bl.route('/transferencia', methods=['POST'])
def hacer_transferencia():
    """
    Registrar una transferencia simulada
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
            - beneficiario
            - banco_destino
          properties:
            user_id:
              type: integer
              example: 1
            amount:
              type: number
              example: 350.50
            beneficiario:
              type: string
              example: "Juan Pérez"
            banco_destino:
              type: string
              example: "Banco del Bienestar"
            concepto:
              type: string
              example: "Renta abril"
    responses:
      201:
        description: Transferencia registrada y wallet actualizado
      400:
        description: Fondos insuficientes u error de validación
      404:
        description: Usuario no encontrado
    """
    data = request.get_json()
    resultado, error = registrar_transferencia(
        engine=current_app.engine,
        user_id=data.get('user_id'),
        amount=data.get('amount'),
        beneficiario=data.get('beneficiario', ''),
        banco_destino=data.get('banco_destino', ''),
        concepto=data.get('concepto', ''),
    )
    if error == "Usuario no encontrado":
        return jsonify({"error": error}), 404
    if error:
        return jsonify({"error": error}), 400
    return jsonify(resultado), 201


@banco_bl.route('/credito/pago', methods=['POST'])
def hacer_pago_credito():
    """
    Registrar un pago al crédito simulado
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
              example: 800.00
    responses:
      201:
        description: Pago registrado, cant_rest y credito_balance actualizados
      400:
        description: Fondos insuficientes, saldo cero o monto inválido
      404:
        description: Usuario no encontrado
    """
    data = request.get_json()
    resultado, error = pagar_credito(
        engine=current_app.engine,
        user_id=data.get('user_id'),
        amount=data.get('amount'),
    )
    if error == "Usuario no encontrado":
        return jsonify({"error": error}), 404
    if error:
        return jsonify({"error": error}), 400
    return jsonify(resultado), 201


@banco_bl.route('/movimientos/<int:user_id>', methods=['GET'])
def get_movimientos(user_id):
    """
    Historial de movimientos bancarios del simulador (transferencias y pagos)
    ---
    tags:
      - wallet
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200:
        description: Lista de movimientos ordenados más reciente primero
      404:
        description: Usuario no encontrado
    """
    meta = MetaData()
    meta.reflect(bind=current_app.engine, only=['usuarios', 'simulacion_movimientos'])

    usuarios_table = meta.tables['usuarios']
    mov_table = meta.tables['simulacion_movimientos']

    with current_app.engine.connect() as conn:
        usuario = conn.execute(
            select(usuarios_table).where(usuarios_table.c.user_id == user_id)
        ).fetchone()
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        rows = conn.execute(
            select(mov_table)
            .where(mov_table.c.user_id == user_id)
            .order_by(desc(mov_table.c.timestamp))
        ).fetchall()

    movimientos = []
    for row in rows:
        data = dict(row._mapping)
        if data.get('timestamp') is not None:
            data['timestamp'] = data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        data['amount'] = float(data['amount']) if data['amount'] is not None else None
        movimientos.append(data)

    return jsonify({
        "user_id": user_id,
        "total": len(movimientos),
        "movimientos": movimientos,
    }), 200
