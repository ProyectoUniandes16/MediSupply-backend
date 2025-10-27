"""
Script de prueba para el microservicio Redis
Prueba operaciones de Cache y Cola
"""
import requests
import json
import time
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "http://localhost:5011"


def print_step(step, description):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.YELLOW}PASO {step}: {description}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")


def print_success(message):
    print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")


def print_error(message):
    print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")


def print_info(message):
    print(f"{Fore.BLUE}ℹ️  {message}{Style.RESET_ALL}")


def test_health():
    """Test 1: Health Check"""
    print_step(1, "Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()
        
        print(json.dumps(data, indent=2))
        
        if response.status_code == 200 and data.get('redis') == 'connected':
            print_success("Servicio y Redis conectados correctamente")
            return True
        else:
            print_error("Servicio degradado")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_cache_operations():
    """Test 2: Operaciones de Cache"""
    print_step(2, "Operaciones de Cache")
    
    # 2.1 Guardar en cache
    print_info("2.1 - Guardando inventarios en cache...")
    inventarios_data = [
        {"id": 1, "cantidad": 50, "ubicacion": "A1"},
        {"id": 2, "cantidad": 30, "ubicacion": "B2"}
    ]
    
    response = requests.post(f"{BASE_URL}/api/cache/", json={
        "key": "inventarios:producto:123",
        "value": inventarios_data,
        "ttl": 3600
    })
    
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 201:
        print_success("Datos guardados en cache")
    else:
        print_error("Error al guardar en cache")
        return False
    
    # 2.2 Leer desde cache
    print_info("\n2.2 - Leyendo desde cache...")
    response = requests.get(f"{BASE_URL}/api/cache/inventarios:producto:123")
    data = response.json()
    
    print(json.dumps(data, indent=2))
    
    if response.status_code == 200:
        print_success("Datos leídos correctamente")
    else:
        print_error("Error al leer cache")
        return False
    
    # 2.3 Verificar existencia
    print_info("\n2.3 - Verificando existencia...")
    response = requests.get(f"{BASE_URL}/api/cache/exists/inventarios:producto:123")
    print(json.dumps(response.json(), indent=2))
    
    # 2.4 Listar claves
    print_info("\n2.4 - Listando claves con patrón...")
    response = requests.get(f"{BASE_URL}/api/cache/keys?pattern=inventarios:*")
    data = response.json()
    print(json.dumps(data, indent=2))
    
    print_success(f"Se encontraron {data['count']} claves")
    
    return True


def test_queue_operations():
    """Test 3: Operaciones de Cola (Pub/Sub)"""
    print_step(3, "Operaciones de Cola (Pub/Sub)")
    
    # 3.1 Publicar mensaje
    print_info("3.1 - Publicando mensaje en canal...")
    
    message_data = {
        "event": "update",
        "producto_id": 123,
        "timestamp": time.time(),
        "data": {
            "cantidad": 45,
            "ubicacion": "A1"
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/queue/publish", json={
        "channel": "inventarios_updates",
        "message": message_data
    })
    
    data = response.json()
    print(json.dumps(data, indent=2))
    
    if response.status_code == 200:
        print_success(f"Mensaje publicado - {data['subscribers']} subscriptores")
    else:
        print_error("Error al publicar mensaje")
        return False
    
    # 3.2 Listar canales
    print_info("\n3.2 - Listando canales activos...")
    response = requests.get(f"{BASE_URL}/api/queue/channels")
    data = response.json()
    print(json.dumps(data, indent=2))
    
    # 3.3 Ver subscriptores
    print_info("\n3.3 - Verificando subscriptores...")
    response = requests.get(f"{BASE_URL}/api/queue/subscribers/inventarios_updates")
    print(json.dumps(response.json(), indent=2))
    
    return True


def test_cache_patterns():
    """Test 4: Operaciones con patrones"""
    print_step(4, "Operaciones con Patrones")
    
    # 4.1 Guardar múltiples claves
    print_info("4.1 - Guardando múltiples productos en cache...")
    
    for producto_id in [100, 200, 300]:
        requests.post(f"{BASE_URL}/api/cache/", json={
            "key": f"inventarios:producto:{producto_id}",
            "value": [{"id": producto_id, "cantidad": producto_id * 10}],
            "ttl": 1800
        })
    
    print_success("Múltiples productos guardados")
    
    # 4.2 Listar con patrón
    print_info("\n4.2 - Listando productos con patrón...")
    response = requests.get(f"{BASE_URL}/api/cache/keys?pattern=inventarios:producto:*")
    data = response.json()
    print(json.dumps(data, indent=2))
    
    print_success(f"Total de productos en cache: {data['count']}")
    
    # 4.3 Eliminar por patrón
    print_info("\n4.3 - Eliminando productos 100-300...")
    response = requests.delete(f"{BASE_URL}/api/cache/pattern/inventarios:producto:*00")
    data = response.json()
    print(json.dumps(data, indent=2))
    
    print_success(f"Eliminadas {data['deleted_count']} claves")
    
    return True


def test_stats():
    """Test 5: Estadísticas"""
    print_step(5, "Estadísticas del Servidor Redis")
    
    response = requests.get(f"{BASE_URL}/stats")
    data = response.json()
    
    print(json.dumps(data, indent=2))
    
    if data.get('status') == 'connected':
        print_success(f"Redis {data.get('redis_version')} - Clientes: {data.get('connected_clients')}")
        print_info(f"Memoria usada: {data.get('used_memory_human')}")
        print_info(f"Canales Pub/Sub: {data.get('pubsub_channels')}")
    
    return True


def cleanup():
    """Limpiar datos de prueba"""
    print_step(6, "Limpieza de Datos de Prueba")
    
    print_info("Eliminando claves de prueba...")
    response = requests.delete(f"{BASE_URL}/api/cache/pattern/inventarios:*")
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Limpieza completada - {data['deleted_count']} claves eliminadas")
    
    return True


def main():
    """Ejecutar todos los tests"""
    print(f"\n{Fore.MAGENTA}{'*'*60}")
    print(f"{Fore.MAGENTA}  TEST DEL MICROSERVICIO REDIS - Puerto 5011")
    print(f"{Fore.MAGENTA}{'*'*60}{Style.RESET_ALL}\n")
    
    tests = [
        ("Health Check", test_health),
        ("Operaciones de Cache", test_cache_operations),
        ("Operaciones de Cola", test_queue_operations),
        ("Patrones de Cache", test_cache_patterns),
        ("Estadísticas", test_stats),
        ("Limpieza", cleanup)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Error en {name}: {e}")
            results.append((name, False))
        
        time.sleep(1)
    
    # Resumen
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.YELLOW}RESUMEN DE PRUEBAS")
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Fore.GREEN}✅ PASS" if result else f"{Fore.RED}❌ FAIL"
        print(f"{status}: {name}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}Total: {passed}/{total} pruebas exitosas{Style.RESET_ALL}\n")
    
    if passed == total:
        print(f"{Fore.GREEN}{'🎉 TODAS LAS PRUEBAS PASARON 🎉':^60}{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.RED}{'⚠️  ALGUNAS PRUEBAS FALLARON ⚠️':^60}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
