"""
Script para probar el microservicio de inventarios manualmente.
Ejecutar después de iniciar docker-compose.
"""

import requests
import json
from time import sleep

BASE_URL = "http://localhost:5009"
API_URL = f"{BASE_URL}/api/inventarios"


def print_response(response, title=""):
    """Imprime una respuesta formateada."""
    print(f"\n{'='*60}")
    if title:
        print(f"{title}")
        print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")


def test_health():
    """Prueba el endpoint de health."""
    print("\n🏥 Probando Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print_response(response, "Health Check")
    return response.status_code == 200


def test_crear_inventario():
    """Prueba crear un inventario."""
    print("\n➕ Probando crear inventario...")
    data = {
        "productoId": "PROD-001",
        "cantidad": 100,
        "ubicacion": "Bodega A - Estante 1",
        "usuario": "admin_test"
    }
    response = requests.post(API_URL, json=data)
    print_response(response, "Crear Inventario")
    
    if response.status_code == 201:
        return response.json()["id"]
    return None


def test_crear_inventario_duplicado():
    """Prueba crear un inventario duplicado (debe fallar)."""
    print("\n⚠️  Probando crear inventario duplicado (debe fallar)...")
    data = {
        "productoId": "PROD-001",
        "cantidad": 50,
        "ubicacion": "Bodega A - Estante 1",
        "usuario": "admin_test"
    }
    response = requests.post(API_URL, json=data)
    print_response(response, "Crear Inventario Duplicado")


def test_crear_inventario_invalido():
    """Prueba crear un inventario con datos inválidos."""
    print("\n❌ Probando crear inventario con datos inválidos...")
    data = {
        "productoId": "PROD-002",
        "cantidad": -10,  # Cantidad negativa (inválida)
        "ubicacion": "Bodega B"
    }
    response = requests.post(API_URL, json=data)
    print_response(response, "Crear Inventario Inválido")


def test_listar_inventarios():
    """Prueba listar inventarios."""
    print("\n📋 Probando listar inventarios...")
    response = requests.get(API_URL)
    print_response(response, "Listar Inventarios")


def test_obtener_inventario(inventario_id):
    """Prueba obtener un inventario por ID."""
    print(f"\n🔍 Probando obtener inventario {inventario_id}...")
    response = requests.get(f"{API_URL}/{inventario_id}")
    print_response(response, "Obtener Inventario")


def test_actualizar_inventario(inventario_id):
    """Prueba actualizar un inventario."""
    print(f"\n✏️  Probando actualizar inventario {inventario_id}...")
    data = {
        "cantidad": 150,
        "ubicacion": "Bodega A - Estante 2",
        "usuario": "admin_test"
    }
    response = requests.put(f"{API_URL}/{inventario_id}", json=data)
    print_response(response, "Actualizar Inventario")


def test_ajustar_cantidad(inventario_id):
    """Prueba ajustar cantidad de un inventario."""
    print(f"\n➕➖ Probando ajustar cantidad del inventario {inventario_id}...")
    
    # Incrementar
    data = {"ajuste": 50, "usuario": "admin_test"}
    response = requests.post(f"{API_URL}/{inventario_id}/ajustar", json=data)
    print_response(response, "Incrementar Cantidad (+50)")
    
    sleep(1)
    
    # Decrementar
    data = {"ajuste": -30, "usuario": "admin_test"}
    response = requests.post(f"{API_URL}/{inventario_id}/ajustar", json=data)
    print_response(response, "Decrementar Cantidad (-30)")


def test_ajustar_cantidad_invalido(inventario_id):
    """Prueba ajustar cantidad a negativo (debe fallar)."""
    print(f"\n⚠️  Probando ajustar cantidad a negativo (debe fallar)...")
    data = {"ajuste": -1000, "usuario": "admin_test"}
    response = requests.post(f"{API_URL}/{inventario_id}/ajustar", json=data)
    print_response(response, "Ajuste Inválido")


def test_filtrar_por_producto():
    """Prueba filtrar inventarios por producto."""
    print("\n🔎 Probando filtrar por producto...")
    response = requests.get(f"{API_URL}?productoId=PROD-001")
    print_response(response, "Filtrar por Producto")


def test_eliminar_inventario(inventario_id):
    """Prueba eliminar un inventario."""
    print(f"\n🗑️  Probando eliminar inventario {inventario_id}...")
    response = requests.delete(f"{API_URL}/{inventario_id}")
    print_response(response, "Eliminar Inventario")


def test_obtener_inventario_inexistente():
    """Prueba obtener un inventario que no existe."""
    print("\n❓ Probando obtener inventario inexistente...")
    response = requests.get(f"{API_URL}/00000000-0000-0000-0000-000000000000")
    print_response(response, "Obtener Inventario Inexistente")


def main():
    """Ejecuta todas las pruebas."""
    print("\n" + "="*60)
    print("🧪 INICIANDO PRUEBAS DEL MICROSERVICIO DE INVENTARIOS")
    print("="*60)
    
    # Health check
    if not test_health():
        print("\n❌ El servicio no está disponible. Verifica que docker-compose esté corriendo.")
        return
    
    sleep(1)
    
    # Crear inventarios
    inventario_id = test_crear_inventario()
    sleep(1)
    
    # Crear otro inventario
    data = {
        "productoId": "PROD-002",
        "cantidad": 200,
        "ubicacion": "Bodega B - Estante 1",
        "usuario": "admin_test"
    }
    response = requests.post(API_URL, json=data)
    print_response(response, "Crear Segundo Inventario")
    sleep(1)
    
    # Probar duplicado
    test_crear_inventario_duplicado()
    sleep(1)
    
    # Probar datos inválidos
    test_crear_inventario_invalido()
    sleep(1)
    
    # Listar
    test_listar_inventarios()
    sleep(1)
    
    if inventario_id:
        # Obtener por ID
        test_obtener_inventario(inventario_id)
        sleep(1)
        
        # Actualizar
        test_actualizar_inventario(inventario_id)
        sleep(1)
        
        # Ajustar cantidades
        test_ajustar_cantidad(inventario_id)
        sleep(1)
        
        # Ajuste inválido
        test_ajustar_cantidad_invalido(inventario_id)
        sleep(1)
    
    # Filtrar
    test_filtrar_por_producto()
    sleep(1)
    
    # Obtener inexistente
    test_obtener_inventario_inexistente()
    sleep(1)
    
    if inventario_id:
        # Eliminar
        test_eliminar_inventario(inventario_id)
        sleep(1)
        
        # Verificar que fue eliminado
        test_obtener_inventario(inventario_id)
    
    print("\n" + "="*60)
    print("✅ PRUEBAS COMPLETADAS")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {str(e)}")
        print("Asegúrate de que el servicio esté corriendo con: docker-compose up")
