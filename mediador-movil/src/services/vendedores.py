
import requests

from src.config.config import Config

class VendedorServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de vendedores."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def obtener_clientes_de_vendedor(vendedor_email: str) -> list:
    """Obtener los clientes asociados a un vendedor."""
    vendedores_url = Config.VENDEDORES_URL

    response = requests.get(
        f"{vendedores_url}/v1/vendedores/clientes?vendedor_email={vendedor_email}",
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code != 200:
        raise VendedorServiceError("Error al obtener los clientes del vendedor", response.status_code)

    return response.json()
    
def listar_vendedores_externo(zona: str = None, estado: str = None, page: int = 1, size: int = 10, filters: dict = None) -> dict:
    """Lista vendedores con paginación y filtros opcionales."""
    vendedores_url = Config.VENDEDORES_URL
    params = {
        "zona": zona,
        "estado": estado,
        "page": page,
        "size": size
    }

    # Agregar filtros adicionales a los parámetros
    if filters:
        params.update(filters)

    print("Parámetros para listar vendedores:", params)

    response = requests.get(
        f"{vendedores_url}/v1/vendedores",
        headers={'Content-Type': 'application/json'},
        params=params
    )

    if response.status_code != 200:
        raise VendedorServiceError("Error al listar los vendedores", response.status_code)

    return response.json()