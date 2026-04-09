from flask import Blueprint, request, jsonify, current_app
from app.simulador.credito_personal import (
    solicitar_credito, obtener_credito,
    pagar_credito_personal, tabla_amortizacion
)
from app.simulador.tarjeta import (
    activar_tarjeta, obtener_tarjeta,
    hacer_cargo, pagar_tarjeta, movimientos_tarjeta
)

productos_bl = Blueprint('productos', __name__, url_prefix='/simulador')


# ── Crédito personal ─────────────────────────────────────────────────────────

@productos_bl.route('/credito/solicitar', methods=['POST'])
def credito_solicitar():
    """
    Solicitar un crédito personal simulado
    ---
    tags:
      - wallet
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [user_id, monto, plazo_meses]
          properties:
            user_id:    { type: integer, example: 1 }
            monto:      { type: number, example: 10000, description: "Entre $1,000 y $50,000" }
            plazo_meses:{ type: integer, example: 12, description: "6, 12, 24 o 36 meses" }
    responses:
      201: { description: Crédito aprobado con tabla de pago }
      400: { description: Ya tienes crédito activo o datos inválidos }
      404: { description: Usuario no encontrado }
    """
    data = request.get_json()
    resultado, error = solicitar_credito(
        engine=current_app.engine,
        user_id=data.get('user_id'),
        monto=data.get('monto'),
        plazo_meses=data.get('plazo_meses'),
    )
    if error == "Usuario no encontrado": return jsonify({"error": error}), 404
    if error: return jsonify({"error": error}), 400
    return jsonify(resultado), 201


@productos_bl.route('/credito/<int:user_id>', methods=['GET'])
def credito_get(user_id):
    """
    Obtener crédito personal activo del usuario
    ---
    tags:
      - wallet
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200: { description: Estado actual del crédito }
      404: { description: Sin crédito activo }
    """
    resultado, error = obtener_credito(engine=current_app.engine, user_id=user_id)
    if error: return jsonify({"error": error}), 404
    return jsonify(resultado), 200


@productos_bl.route('/credito/pagar', methods=['POST'])
def credito_pagar():
    """
    Pagar cuota del crédito personal simulado
    ---
    tags:
      - wallet
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [user_id, monto]
          properties:
            user_id: { type: integer, example: 1 }
            monto:   { type: number, example: 1200.00 }
    responses:
      201: { description: Pago registrado, capital e interés desglosados }
      400: { description: Fondos insuficientes o sin crédito activo }
      404: { description: Usuario no encontrado }
    """
    data = request.get_json()
    resultado, error = pagar_credito_personal(
        engine=current_app.engine,
        user_id=data.get('user_id'),
        monto_pago=data.get('monto'),
    )
    if error == "Usuario no encontrado": return jsonify({"error": error}), 404
    if error: return jsonify({"error": error}), 400
    return jsonify(resultado), 201


@productos_bl.route('/credito/tabla/<int:user_id>', methods=['GET'])
def credito_tabla(user_id):
    """
    Tabla de amortización del crédito activo
    ---
    tags:
      - wallet
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200: { description: Tabla de pagos restantes }
      404: { description: Sin crédito activo }
    """
    resultado, error = tabla_amortizacion(engine=current_app.engine, user_id=user_id)
    if error: return jsonify({"error": error}), 404
    return jsonify(resultado), 200


# ── Tarjeta de crédito ───────────────────────────────────────────────────────

@productos_bl.route('/tarjeta/activar', methods=['POST'])
def tarjeta_activar():
    """
    Activar tarjeta de crédito simulada
    ---
    tags:
      - wallet
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [user_id, limite_credito]
          properties:
            user_id:        { type: integer, example: 1 }
            limite_credito: { type: number, example: 10000, description: "Entre $1,000 y $20,000" }
            dia_corte:      { type: integer, example: 15, description: "Día del mes 1-28, default 15" }
    responses:
      201: { description: Tarjeta activada con fecha de corte y límite de pago }
      400: { description: Ya tienes tarjeta activa o datos inválidos }
      404: { description: Usuario no encontrado }
    """
    data = request.get_json()
    resultado, error = activar_tarjeta(
        engine=current_app.engine,
        user_id=data.get('user_id'),
        limite_credito=data.get('limite_credito'),
        dia_corte=data.get('dia_corte', 15),
    )
    if error == "Usuario no encontrado": return jsonify({"error": error}), 404
    if error: return jsonify({"error": error}), 400
    return jsonify(resultado), 201


@productos_bl.route('/tarjeta/<int:user_id>', methods=['GET'])
def tarjeta_get(user_id):
    """
    Obtener tarjeta de crédito activa del usuario
    ---
    tags:
      - wallet
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200: { description: Estado de la tarjeta con saldo, límite, fecha corte y pago mínimo }
      404: { description: Sin tarjeta activa }
    """
    resultado, error = obtener_tarjeta(engine=current_app.engine, user_id=user_id)
    if error: return jsonify({"error": error}), 404
    return jsonify(resultado), 200


@productos_bl.route('/tarjeta/cargo', methods=['POST'])
def tarjeta_cargo():
    """
    Hacer un cargo a la tarjeta de crédito simulada
    ---
    tags:
      - wallet
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [user_id, monto]
          properties:
            user_id:     { type: integer, example: 1 }
            monto:       { type: number, example: 1500.00 }
            descripcion: { type: string, example: "Compra en tienda" }
    responses:
      201: { description: Cargo registrado, saldo y disponible actualizados }
      400: { description: Crédito insuficiente o sin tarjeta activa }
      404: { description: Usuario no encontrado }
    """
    data = request.get_json()
    resultado, error = hacer_cargo(
        engine=current_app.engine,
        user_id=data.get('user_id'),
        monto=data.get('monto'),
        descripcion=data.get('descripcion', ''),
    )
    if error == "Usuario no encontrado": return jsonify({"error": error}), 404
    if error: return jsonify({"error": error}), 400
    return jsonify(resultado), 201


@productos_bl.route('/tarjeta/pagar', methods=['POST'])
def tarjeta_pagar():
    """
    Pagar saldo de la tarjeta de crédito simulada
    ---
    tags:
      - wallet
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [user_id, monto]
          properties:
            user_id: { type: integer, example: 1 }
            monto:   { type: number, example: 2000.00, description: "Pagar mínimo, total o cualquier monto" }
    responses:
      201: { description: Pago registrado, nueva fecha corte y pago mínimo actualizados }
      400: { description: Fondos insuficientes, sin saldo o sin tarjeta activa }
      404: { description: Usuario no encontrado }
    """
    data = request.get_json()
    resultado, error = pagar_tarjeta(
        engine=current_app.engine,
        user_id=data.get('user_id'),
        monto_pago=data.get('monto'),
    )
    if error == "Usuario no encontrado": return jsonify({"error": error}), 404
    if error: return jsonify({"error": error}), 400
    return jsonify(resultado), 201


@productos_bl.route('/tarjeta/movimientos/<int:user_id>', methods=['GET'])
def tarjeta_movimientos(user_id):
    """
    Movimientos de la tarjeta de crédito simulada
    ---
    tags:
      - wallet
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200: { description: Lista de cargos y pagos }
      404: { description: Sin tarjeta activa }
    """
    resultado, error = movimientos_tarjeta(engine=current_app.engine, user_id=user_id)
    if error: return jsonify({"error": error}), 404
    return jsonify(resultado), 200
