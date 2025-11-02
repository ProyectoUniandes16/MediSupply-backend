from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from src.services.vendedores import (
    crear_vendedor_externo, 
    listar_vendedores, 
    VendedorServiceError, 
    obtener_detalle_vendedor_externo,
    crear_plan_venta_externo,
    listar_planes_venta_externo,
    obtener_plan_venta_externo
)

# Crear el blueprint para vendedores
vendedores_bp = Blueprint('vendedor', __name__)

@vendedores_bp.route('/vendedor', methods=['POST'])
@jwt_required()
def crear_vendedor():
    """
    Endpoint del BFF para crear un vendedor.
    Delega la lógica de negocio al servicio de vendedores.
    """
    try:
        datos_vendedor = request.get_json()
        
        # Llamar a la capa de servicio para manejar la lógica
        datos_respuesta = crear_vendedor_externo(datos_vendedor)
        
        return jsonify(datos_respuesta), 201

    except VendedorServiceError as e:
        # Capturar errores controlados desde la capa de servicio
        return jsonify(e.message), e.status_code

    except Exception as e:
        # Capturar cualquier otro error no esperado
        current_app.logger.error(f"Error inesperado en el blueprint de vendedor: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500

@vendedores_bp.route('/vendedor', methods=['GET'])
@jwt_required()
def obtener_vendedores():
    """
    Endpoint del BFF para listar vendedores.
    Soporta filtros opcionales por zona y estado, además de paginación.
    
    Query params:
        - zona (str, optional): Filtrar por zona
        - estado (str, optional): Filtrar por estado (ej: activo, inactivo)
        - page (int, optional): Número de página (default: 1)
        - size (int, optional): Tamaño de página (default: 10)
    """
    try:
        # Obtener parámetros de consulta
        zona = request.args.get('zona')
        estado = request.args.get('estado')
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        
        # Validar parámetros de paginación
        if page < 1:
            return jsonify({'error': 'El número de página debe ser mayor a 0'}), 400
        if size < 1 or size > 100:
            return jsonify({'error': 'El tamaño de página debe estar entre 1 y 100'}), 400
        
        # Llamar a la capa de servicio
        datos_respuesta = listar_vendedores(zona=zona, estado=estado, page=page, size=size)
        
        return jsonify(datos_respuesta), 200

    except VendedorServiceError as e:
        # Capturar errores controlados desde la capa de servicio
        return jsonify(e.message), e.status_code

    except ValueError as e:
        # Error en conversión de parámetros numéricos
        return jsonify({
            'error': 'Parámetros inválidos',
            'message': 'Los parámetros page y size deben ser números enteros'
        }), 400

    except Exception as e:
        # Capturar cualquier otro error no esperado
        current_app.logger.error(f"Error inesperado al listar vendedores: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500

@vendedores_bp.route('/vendedor/<string:vendedor_id>', methods=['GET'])
@jwt_required()
def obtener_detalle_vendedor(vendedor_id):
    """
    Endpoint del BFF para obtener el detalle completo de un vendedor.
    Delega al microservicio de vendedores.
    """
    try:
        detalle = obtener_detalle_vendedor_externo(vendedor_id)
        return jsonify({'data': detalle}), 200
    except VendedorServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error inesperado obteniendo detalle de vendedor {vendedor_id}: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INESPERADO'
        }), 500


@vendedores_bp.route('/planes-venta', methods=['POST'])
@jwt_required()
def crear_plan_venta():
    """
    Endpoint del BFF para crear un plan de venta.
    Delega la lógica de negocio al servicio de vendedores.
    
    Request Body:
        {
            "nombre_plan": "Plan Q1 2025",
            "gerente_id": "uuid-gerente",
            "vendedores_ids": ["uuid-vendedor-1", "uuid-vendedor-2"],
            "periodo": "2025-01",
            "meta_ingresos": 50000.00,
            "meta_visitas": 100,
            "meta_clientes_nuevos": 20,
            "estado": "activo"  // opcional
        }
    
    Returns:
        201: Plan creado exitosamente
        200: Plan actualizado exitosamente (si se proporciona plan_id)
        400: Error de validación
        404: Vendedor no encontrado
        409: Conflicto de concurrencia
    """
    try:
        datos_plan = request.get_json()
        
        # Llamar a la capa de servicio
        datos_respuesta = crear_plan_venta_externo(datos_plan)
        
        # Si fue creado, retornar 201; si fue actualizado, retornar 200
        status_code = 201 if datos_respuesta.get("operacion") == "crear" else 200
        
        return jsonify(datos_respuesta), status_code

    except VendedorServiceError as e:
        # Capturar errores controlados desde la capa de servicio
        return jsonify(e.message), e.status_code

    except Exception as e:
        # Capturar cualquier otro error no esperado
        current_app.logger.error(f"Error inesperado en crear plan de venta: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500


@vendedores_bp.route('/planes-venta', methods=['GET'])
@jwt_required()
def listar_planes_venta():
    """
    Endpoint del BFF para listar planes de venta.
    Soporta filtros opcionales y paginación.
    
    Query params:
        - vendedor_id (str, optional): Filtrar por vendedor
        - periodo (str, optional): Filtrar por periodo (YYYY-MM)
        - estado (str, optional): Filtrar por estado
        - nombre_plan (str, optional): Filtrar por nombre del plan (búsqueda parcial)
        - page (int, optional): Número de página (default: 1)
        - size (int, optional): Tamaño de página (default: 10)
    """
    try:
        # Obtener parámetros de consulta
        vendedor_id = request.args.get('vendedor_id')
        periodo = request.args.get('periodo')
        estado = request.args.get('estado')
        nombre_plan = request.args.get('nombre_plan')
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        
        # Validar parámetros de paginación
        if page < 1:
            return jsonify({'error': 'El número de página debe ser mayor a 0'}), 400
        if size < 1 or size > 100:
            return jsonify({'error': 'El tamaño de página debe estar entre 1 y 100'}), 400
        
        # Llamar a la capa de servicio
        datos_respuesta = listar_planes_venta_externo(
            vendedor_id=vendedor_id,
            periodo=periodo,
            estado=estado,
            nombre_plan=nombre_plan,
            page=page,
            size=size
        )
        
        return jsonify(datos_respuesta), 200

    except VendedorServiceError as e:
        # Capturar errores controlados desde la capa de servicio
        return jsonify(e.message), e.status_code

    except ValueError as e:
        # Error en conversión de parámetros numéricos
        return jsonify({
            'error': 'Parámetros inválidos',
            'message': 'Los parámetros page y size deben ser números enteros'
        }), 400

    except Exception as e:
        # Capturar cualquier otro error no esperado
        current_app.logger.error(f"Error inesperado al listar planes de venta: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500


@vendedores_bp.route('/planes-venta/<string:plan_id>', methods=['GET'])
@jwt_required()
def obtener_detalle_plan_venta(plan_id):
    """
    Endpoint del BFF para obtener el detalle completo de un plan de venta.
    Delega al microservicio de vendedores.
    """
    try:
        detalle = obtener_plan_venta_externo(plan_id)
        return jsonify({'data': detalle}), 200
    except VendedorServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error inesperado obteniendo detalle de plan de venta {plan_id}: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INESPERADO'
        }), 500

