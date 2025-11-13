"""
Servicio de optimización de rutas usando OpenRouteService API
"""
import os
import requests
import folium
from flask import current_app


class RutaServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de rutas."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# Obtener la clave de API de las variables de entorno
ORS_API_KEY = os.getenv("ORS_API_KEY", "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjQ5M2RlMmQzNDkzOTRjZGU4ZWYyY2YxZmRhYTlhZDBlIiwiaCI6Im11cm11cjY0In0=")


def obtener_geometria_ruta_detallada(puntos_ordenados):
    """
    Llama a la API de Direcciones de ORS para obtener la geometría detallada de la ruta.
    
    Args:
        puntos_ordenados: Una lista de coordenadas [lng, lat] en el orden óptimo.
    
    Returns:
        Una lista de coordenadas [lat, lng] para usar con Folium.
    """
    if not ORS_API_KEY:
        current_app.logger.error("ORS_API_KEY no está configurada")
        return None
    
    # El cuerpo de la solicitud para la API de Direcciones
    body = {"coordinates": puntos_ordenados}
    
    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': ORS_API_KEY
    }
    
    try:
        # Llamada a la API de Direcciones
        res = requests.post(
            'https://api.openrouteservice.org/v2/directions/driving-car/geojson', 
            json=body, 
            headers=headers,
            timeout=30
        )

        if res.status_code != 200:
            current_app.logger.error(f"Error en la API de Direcciones: {res.text}")
            return None

        # Extraemos la geometría de la respuesta
        respuesta_json = res.json()
        geometria = respuesta_json['features'][0]['geometry']['coordinates']
        
        # La API devuelve [lng, lat], Folium necesita [lat, lng]. Las intercambiamos.
        geometria_folium = [[coord[1], coord[0]] for coord in geometria]
        
        return geometria_folium
    
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error al obtener geometría de ruta: {str(e)}")
        return None


def generar_mapa_ruta_html(bodega, orden_destinos, ruta_detallada):
    """
    Genera un mapa HTML con la ruta óptima usando Folium.
    
    Args:
        bodega: Coordenadas de la bodega [lng, lat]
        orden_destinos: Lista de destinos en orden óptimo
        ruta_detallada: Geometría detallada de la ruta
        
    Returns:
        String con el HTML del mapa
    """
    # Convertir coordenadas de bodega a formato Folium [lat, lng]
    bodega_folium = [bodega[1], bodega[0]]
    
    # Crear mapa centrado en la bodega
    mapa = folium.Map(location=bodega_folium, zoom_start=12)
    
    # Marcador de bodega/inicio
    folium.Marker(
        location=bodega_folium,
        popup="<b>Bodega / Centro de distribución</b>",
        icon=folium.Icon(color="green", icon="home", prefix="fa")
    ).add_to(mapa)
    
    # Añadir marcadores de destinos
    destino_num = 1
    for step in orden_destinos:
        if step["job_id"] == "inicio/fin":
            continue
        
        ubicacion = step["ubicacion"]
        ubicacion_folium = [ubicacion[1], ubicacion[0]]
        
        folium.Marker(
            location=ubicacion_folium,
            popup=f"<b>Destino {destino_num}</b><br>Orden: {step['job_id']}",
            icon=folium.Icon(color="blue", icon="flag", prefix="fa"),
        ).add_to(mapa)
        destino_num += 1
    
    # Dibujar ruta
    if ruta_detallada:
        # Ruta detallada por calles
        folium.PolyLine(
            ruta_detallada, 
            color="red", 
            weight=4, 
            opacity=0.8,
            tooltip="Ruta óptima por calles"
        ).add_to(mapa)
    else:
        # Método de respaldo con líneas rectas
        puntos_rectos = [bodega_folium] + [
            [d['ubicacion'][1], d['ubicacion'][0]] 
            for d in orden_destinos if d['job_id'] != 'inicio/fin'
        ] + [bodega_folium]
        
        folium.PolyLine(
            puntos_rectos, 
            color="orange", 
            weight=2, 
            opacity=0.8, 
            tooltip="Ruta directa (sin detalle de calles)"
        ).add_to(mapa)
    
    # Convertir el mapa a HTML
    html_map = mapa._repr_html_()
    
    return html_map


def optimizar_ruta(bodega, destinos):
    """
    Optimiza la ruta de entrega desde una bodega hacia múltiples destinos.
    
    Args:
        bodega: Coordenadas de la bodega [lng, lat]
        destinos: Lista de coordenadas de destinos [[lng, lat], ...]
        
    Returns:
        dict: Contiene el orden óptimo, resumen y mapa HTML
        
    Raises:
        RutaServiceError: Si ocurre un error en la optimización
    """
    # Validaciones
    if not bodega or len(bodega) != 2:
        raise RutaServiceError({
            'error': 'Coordenadas de bodega inválidas. Debe ser [longitud, latitud]',
            'codigo': 'BODEGA_INVALIDA'
        }, 400)
    
    if not destinos or len(destinos) < 1:
        raise RutaServiceError({
            'error': 'Debes enviar al menos 1 destino',
            'codigo': 'DESTINOS_INSUFICIENTES'
        }, 400)
    
    # Validar que cada destino tenga 2 coordenadas
    for i, destino in enumerate(destinos):
        if not destino or len(destino) != 2:
            raise RutaServiceError({
                'error': f'Destino {i+1} tiene coordenadas inválidas. Debe ser [longitud, latitud]',
                'codigo': 'DESTINO_INVALIDO'
            }, 400)
    
    if not ORS_API_KEY:
        raise RutaServiceError({
            'error': 'La clave de API de OpenRouteService no está configurada',
            'codigo': 'API_KEY_NO_CONFIGURADA'
        }, 500)
    
    try:
        # 1. Preparar payload para la optimización
        jobs = [
            {
                "id": i + 1,
                "service": 300,  # 5 minutos de servicio por entrega
                "location": destino
            }
            for i, destino in enumerate(destinos)
        ]
        
        payload = {
            "jobs": jobs,
            "vehicles": [{
                "id": 1,
                "profile": "driving-car",
                "start": bodega,
                "end": bodega
            }]
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": ORS_API_KEY
        }
        
        # 2. Llamada a la API de Optimización
        current_app.logger.info(f"Optimizando ruta con {len(destinos)} destinos...")
        
        response_opt = requests.post(
            "https://api.openrouteservice.org/optimization",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response_opt.status_code != 200:
            current_app.logger.error(f"Error en ORS Optimization: {response_opt.text}")
            raise RutaServiceError({
                'error': 'Error en el servicio de optimización de rutas',
                'codigo': 'ERROR_OPTIMIZACION',
                'detalle': response_opt.text
            }, response_opt.status_code)
        
        data_opt = response_opt.json()
        steps = data_opt["routes"][0]["steps"]
        
        # Extraer orden de destinos
        orden_destinos = [
            {
                "job_id": step.get("job", "inicio/fin"),
                "ubicacion": step.get("location")
            }
            for step in steps
        ]
        
        # 3. Obtener geometría detallada de la ruta
        puntos_ordenados_para_ruta = [step["ubicacion"] for step in orden_destinos]
        ruta_detallada = obtener_geometria_ruta_detallada(puntos_ordenados_para_ruta)
        
        # 4. Generar mapa HTML
        html_mapa = generar_mapa_ruta_html(bodega, orden_destinos, ruta_detallada)
        
        # 5. Preparar respuesta
        resumen = data_opt.get("summary", {})
        
        return {
            "orden_optimo": orden_destinos,
            "resumen": {
                "distancia_total_metros": resumen.get("distance", 0),
                "tiempo_total_segundos": resumen.get("duration", 0),
                "tiempo_servicio_segundos": resumen.get("service", 0),
                "costo": resumen.get("cost", 0)
            },
            "mapa_html": html_mapa
        }
        
    except requests.exceptions.Timeout:
        current_app.logger.error("Timeout al llamar a la API de OpenRouteService")
        raise RutaServiceError({
            'error': 'Timeout al conectar con el servicio de rutas',
            'codigo': 'TIMEOUT_API'
        }, 504)
    
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con OpenRouteService: {str(e)}")
        raise RutaServiceError({
            'error': 'Error de conexión con el servicio de rutas',
            'codigo': 'ERROR_CONEXION_API',
            'detalle': str(e)
        }, 503)
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado al optimizar ruta: {str(e)}")
        raise RutaServiceError({
            'error': 'Error inesperado al optimizar ruta',
            'codigo': 'ERROR_INESPERADO',
            'detalle': str(e)
        }, 500)
