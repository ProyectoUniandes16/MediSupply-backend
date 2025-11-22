"""
Blueprint para la optimización de rutas de entrega
"""
from flask import Blueprint, request, jsonify, current_app, Response
from src.services.ruta_service import (
    optimizar_ruta, 
    RutaServiceError, 
    crear_ruta_entrega,
    listar_rutas,
    obtener_ruta_por_id
)
from src.models.ruta import Ruta, DetalleRuta
from src.models.zona import db


# Crear el blueprint para rutas
rutas_bp = Blueprint('rutas', __name__)


@rutas_bp.route('/ruta-optima', methods=['POST'])
def generar_ruta_optima():
    """
    Endpoint para generar una ruta óptima de entrega.
    
    Request Body:
        {
            "bodega": [-74.08175, 4.60971],
            "destinos": [
                [-74.0445, 4.6760],
                [-74.1475, 4.6165],
                [-74.1253, 4.7010]
            ]
        }
    
    Returns:
        HTML del mapa con la ruta óptima o JSON con detalles de la ruta
        
    Query Params:
        - formato: 'html' (default) o 'json'
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'codigo': 'DATOS_FALTANTES'
            }), 400
        
        bodega = data.get('bodega')
        destinos = data.get('destinos')
        
        # Obtener formato de respuesta (html por defecto)
        formato = request.args.get('formato', 'html').lower()
        
        # Validaciones básicas
        if not bodega:
            return jsonify({
                'error': 'Campo "bodega" es requerido',
                'codigo': 'BODEGA_REQUERIDA'
            }), 400
        
        if not destinos:
            return jsonify({
                'error': 'Campo "destinos" es requerido',
                'codigo': 'DESTINOS_REQUERIDOS'
            }), 400
        
        # Llamar al servicio de optimización
        resultado = optimizar_ruta(bodega, destinos)
        
        # Retornar según el formato solicitado
        if formato == 'json':
            # Retornar datos sin el HTML del mapa
            return jsonify({
                'orden_optimo': resultado['orden_optimo'],
                'resumen': resultado['resumen'],
                'mensaje': 'Ruta optimizada exitosamente'
            }), 200
        else:
            # Retornar HTML del mapa (formato por defecto)
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ruta Óptima de Entrega - MediSupply</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .header p {{
            margin: 5px 0 0 0;
            opacity: 0.9;
            font-size: 14px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        .info-panel {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .info-panel h2 {{
            margin-top: 0;
            color: #333;
            font-size: 18px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .stat-box {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-top: 5px;
        }}
        .map-container {{
            background: white;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .orden-lista {{
            list-style: none;
            padding: 0;
            margin: 15px 0 0 0;
        }}
        .orden-item {{
            background: #f8f9fa;
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 6px;
            border-left: 4px solid #28a745;
        }}
        .orden-item.inicio {{
            border-left-color: #667eea;
        }}
        .orden-numero {{
            font-weight: bold;
            color: #667eea;
            margin-right: 10px;
        }}
        .coordenadas {{
            color: #666;
            font-size: 12px;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚚 Ruta Óptima de Entrega</h1>
        <p>Sistema de Optimización de Rutas - MediSupply Logística</p>
    </div>
    
    <div class="container">
        <div class="info-panel">
            <h2>📊 Resumen de la Ruta</h2>
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-label">Tiempo Total</div>
                    <div class="stat-value">{resultado['resumen']['tiempo_total_segundos'] / 60:.0f} min</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Destinos</div>
                    <div class="stat-value">{len([d for d in resultado['orden_optimo'] if d['job_id'] != 'inicio/fin'])}</div>
                </div>
            </div>
        </div>
        
        <div class="info-panel">
            <h2>📍 Orden de Entrega</h2>
            <ul class="orden-lista">
"""
            
            # Agregar orden de destinos
            for i, destino in enumerate(resultado['orden_optimo']):
                if destino['job_id'] == 'inicio/fin':
                    if i == 0:
                        html_content += f"""
                <li class="orden-item inicio">
                    <span class="orden-numero">🏠 Inicio:</span> Bodega / Centro de Distribución
                    <div class="coordenadas">Coordenadas: {destino['ubicacion']}</div>
                </li>
"""
                    else:
                        html_content += f"""
                <li class="orden-item inicio">
                    <span class="orden-numero">🏁 Fin:</span> Regreso a Bodega
                    <div class="coordenadas">Coordenadas: {destino['ubicacion']}</div>
                </li>
"""
                else:
                    html_content += f"""
                <li class="orden-item">
                    <span class="orden-numero">📦 Destino {destino['job_id']}:</span> Punto de Entrega
                    <div class="coordenadas">Coordenadas: {destino['ubicacion']}</div>
                </li>
"""
            
            html_content += """
            </ul>
        </div>
        
        <div class="map-container">
"""
            html_content += resultado['mapa_html']
            html_content += """
        </div>
    </div>
</body>
</html>
"""
            
            return Response(html_content, mimetype='text/html')
    
    except RutaServiceError as e:
        return jsonify(e.message), e.status_code
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado en ruta óptima: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
            'detalle': str(e)
        }), 500


@rutas_bp.route('/rutas', methods=['POST'])
def crear_ruta():
    """
    Endpoint para crear una nueva ruta de entrega.
    
    Request Body:
        {
            "ruta": [
                {
                    "ubicacion": [-74.1475, 4.6165],
                    "pedido_id": "20f7a15a-069e-4019-afbd-dae3ca0914a1"
                },
                {
                    "ubicacion": [-74.0445, 4.6760],
                    "pedido_id": "20f7a15a-069e-4019-afbd-dae3ca0914a1"
                }
            ],
            "bodega_id": "20f7a15a-069e-4019-afbd-dae3ca0914a1",
            "camion_id": "74c716fd-1e05-4291-8935-4ac8904c6964",
            "zona_id": "74c716fd-1e05-4291-8935-4ac8904c6964",
            "estado": "iniciado"
        }
    
    Returns:
        JSON con los datos de la ruta creada
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No se proporcionaron datos',
                'codigo': 'DATOS_FALTANTES'
            }), 400
        
        # Validar campos requeridos
        campos_requeridos = ['ruta', 'bodega_id', 'camion_id', 'zona_id', 'estado']
        campos_faltantes = [campo for campo in campos_requeridos if campo not in data]
        
        if campos_faltantes:
            return jsonify({
                'error': f'Campos requeridos faltantes: {", ".join(campos_faltantes)}',
                'codigo': 'CAMPOS_REQUERIDOS',
                'campos_faltantes': campos_faltantes
            }), 400
        
        # Validar que ruta sea una lista y no esté vacía
        if not isinstance(data['ruta'], list) or len(data['ruta']) == 0:
            return jsonify({
                'error': 'El campo "ruta" debe ser una lista con al menos un elemento',
                'codigo': 'RUTA_INVALIDA'
            }), 400
        
        # Validar cada punto de la ruta
        for i, punto in enumerate(data['ruta']):
            if 'ubicacion' not in punto or 'pedido_id' not in punto:
                return jsonify({
                    'error': f'El punto {i+1} de la ruta debe contener: ubicacion y pedido_id',
                    'codigo': 'PUNTO_RUTA_INVALIDO',
                    'punto_indice': i
                }), 400
            
            if not isinstance(punto['ubicacion'], list) or len(punto['ubicacion']) != 2:
                return jsonify({
                    'error': f'La ubicación del punto {i+1} debe ser [longitud, latitud]',
                    'codigo': 'UBICACION_INVALIDA',
                    'punto_indice': i
                }), 400
        
        # Validar estados permitidos
        estados_validos = ['pendiente', 'iniciado', 'en_progreso', 'completado', 'cancelado']
        if data['estado'] not in estados_validos:
            return jsonify({
                'error': f'Estado inválido. Estados permitidos: {", ".join(estados_validos)}',
                'codigo': 'ESTADO_INVALIDO',
                'estados_validos': estados_validos
            }), 400
        
        # Llamar al servicio para crear la ruta
        nueva_ruta = crear_ruta_entrega(
            bodega_id=data['bodega_id'],
            camion_id=data['camion_id'],
            zona_id=data['zona_id'],
            estado=data['estado'],
            puntos_ruta=data['ruta']
        )
        
        return jsonify({
            'mensaje': 'Ruta creada exitosamente',
            'ruta': nueva_ruta.to_dict_with_details()
        }), 201
    
    except RutaServiceError as e:
        return jsonify(e.message), e.status_code
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado al crear ruta: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
            'detalle': str(e)
        }), 500


@rutas_bp.route('/rutas', methods=['GET'])
def listar_rutas_endpoint():
    """
    Endpoint para listar rutas con filtros opcionales.
    
    Query Params:
        - estado: Estado de la ruta (pendiente, iniciado, en_progreso, completado, cancelado)
        - zona_id: ID de la zona
        - camion_id: ID del camión
        - bodega_id: ID de la bodega
        
    Returns:
        JSON con la lista de rutas y total
    """
    try:
        # Obtener filtros de los query params
        filtros = {}
        
        if request.args.get('estado'):
            filtros['estado'] = request.args.get('estado')
        
        if request.args.get('zona_id'):
            filtros['zona_id'] = request.args.get('zona_id')
        
        if request.args.get('camion_id'):
            filtros['camion_id'] = request.args.get('camion_id')
        
        if request.args.get('bodega_id'):
            filtros['bodega_id'] = request.args.get('bodega_id')
        
        resultado = listar_rutas(filtros if filtros else None)
        return jsonify(resultado), 200
    
    except RutaServiceError as e:
        return jsonify(e.message), e.status_code
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado al listar rutas: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
            'detalle': str(e)
        }), 500


@rutas_bp.route('/rutas/<ruta_id>', methods=['GET'])
def obtener_ruta_endpoint(ruta_id):
    """
    Endpoint para obtener una ruta específica por su ID.
    
    Args:
        ruta_id (str): ID de la ruta a consultar
        
    Returns:
        JSON con los datos de la ruta y sus detalles
    """
    try:
        resultado = obtener_ruta_por_id(ruta_id)
        return jsonify(resultado), 200
    
    except RutaServiceError as e:
        return jsonify(e.message), e.status_code
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado al obtener ruta: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INTERNO_SERVIDOR',
            'detalle': str(e)
        }), 500

