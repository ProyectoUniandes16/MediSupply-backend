"""
Blueprint para la optimización de rutas de entrega
"""
from flask import Blueprint, request, jsonify, current_app, Response
from src.services.ruta_service import optimizar_ruta, RutaServiceError


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
