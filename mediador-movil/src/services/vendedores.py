
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