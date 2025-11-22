"""
Tests para los endpoints GET /rutas en logistica blueprint
"""
import pytest
from unittest.mock import patch
from src import create_app
from flask_jwt_extended import create_access_token
from src.services.logistica import LogisticaServiceError


class TestListarRutasBlueprint:
    """Tests para el endpoint GET /rutas"""

    @patch('src.blueprints.logistica.listar_rutas_logistica')
    def test_listar_rutas_success(self, mock_listar):
        """Test listar rutas exitosamente"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        mock_listar.return_value = {
            "rutas": [
                {"id": 1, "estado": "pendiente"},
                {"id": 2, "estado": "en_progreso"}
            ]
        }

        response = client.get('/rutas', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.get_json()
        assert "rutas" in data
        assert len(data["rutas"]) == 2
        mock_listar.assert_called_once_with(None)

    @patch('src.blueprints.logistica.listar_rutas_logistica')
    def test_listar_rutas_con_filtro_estado(self, mock_listar):
        """Test listar rutas con filtro de estado"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        mock_listar.return_value = {"rutas": [{"id": 1, "estado": "pendiente"}]}

        response = client.get('/rutas?estado=pendiente', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        mock_listar.assert_called_once()
        call_args = mock_listar.call_args[0][0]  # Primer argumento posicional
        assert call_args['estado'] == 'pendiente'

    @patch('src.blueprints.logistica.listar_rutas_logistica')
    def test_listar_rutas_con_filtro_zona_id(self, mock_listar):
        """Test listar rutas con filtro de zona_id"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        mock_listar.return_value = {"rutas": []}

        response = client.get('/rutas?zona_id=5', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        mock_listar.assert_called_once()
        call_args = mock_listar.call_args[0][0]
        assert call_args['zona_id'] == '5'

    @patch('src.blueprints.logistica.listar_rutas_logistica')
    def test_listar_rutas_con_filtro_camion_id(self, mock_listar):
        """Test listar rutas con filtro de camion_id"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        mock_listar.return_value = {"rutas": []}

        response = client.get('/rutas?camion_id=3', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        mock_listar.assert_called_once()
        call_args = mock_listar.call_args[0][0]
        assert call_args['camion_id'] == '3'

    @patch('src.blueprints.logistica.listar_rutas_logistica')
    def test_listar_rutas_con_filtro_bodega_id(self, mock_listar):
        """Test listar rutas con filtro de bodega_id"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        mock_listar.return_value = {"rutas": []}

        response = client.get('/rutas?bodega_id=2', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        mock_listar.assert_called_once()
        call_args = mock_listar.call_args[0][0]
        assert call_args['bodega_id'] == '2'

    @patch('src.blueprints.logistica.listar_rutas_logistica')
    def test_listar_rutas_sin_token(self, mock_listar):
        """Test listar rutas sin token JWT"""
        app = create_app()
        client = app.test_client()

        response = client.get('/rutas')

        assert response.status_code == 401
        mock_listar.assert_not_called()

    @patch('src.blueprints.logistica.listar_rutas_logistica')
    def test_listar_rutas_service_error(self, mock_listar):
        """Test listar rutas con error del servicio"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        mock_listar.side_effect = LogisticaServiceError("Error al consultar", 500)

        response = client.get('/rutas', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data

    @patch('src.blueprints.logistica.listar_rutas_logistica')
    def test_listar_rutas_unexpected_error(self, mock_listar):
        """Test listar rutas con error inesperado"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        mock_listar.side_effect = Exception("Error inesperado")

        response = client.get('/rutas', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data


class TestObtenerRutaDetalladaBlueprint:
    """Tests para el endpoint GET /rutas/<ruta_id>"""

    @patch('src.blueprints.logistica.obtener_ruta_detallada')
    def test_obtener_ruta_success(self, mock_obtener):
        """Test obtener ruta detallada exitosamente"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        mock_obtener.return_value = {
            "id": 1,
            "estado": "pendiente",
            "detalles": [{"orden": 1, "pedido_id": "P001"}]
        }

        response = client.get('/rutas/1', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == 1
        assert "detalles" in data
        mock_obtener.assert_called_once_with("1")

    @patch('src.blueprints.logistica.obtener_ruta_detallada')
    def test_obtener_ruta_not_found(self, mock_obtener):
        """Test obtener ruta que no existe"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        mock_obtener.side_effect = LogisticaServiceError("Ruta no encontrada", 404)

        response = client.get('/rutas/999', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    @patch('src.blueprints.logistica.obtener_ruta_detallada')
    def test_obtener_ruta_sin_token(self, mock_obtener):
        """Test obtener ruta sin token JWT"""
        app = create_app()
        client = app.test_client()

        response = client.get('/rutas/1')

        assert response.status_code == 401
        mock_obtener.assert_not_called()

    @patch('src.blueprints.logistica.obtener_ruta_detallada')
    def test_obtener_ruta_service_error(self, mock_obtener):
        """Test obtener ruta con error del servicio"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        mock_obtener.side_effect = LogisticaServiceError("Error interno", 500)

        response = client.get('/rutas/1', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data

    @patch('src.blueprints.logistica.obtener_ruta_detallada')
    def test_obtener_ruta_unexpected_error(self, mock_obtener):
        """Test obtener ruta con error inesperado"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        mock_obtener.side_effect = Exception("Error inesperado")

        response = client.get('/rutas/1', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data

    @patch('src.blueprints.logistica.obtener_ruta_detallada')
    def test_obtener_ruta_con_uuid(self, mock_obtener):
        """Test obtener ruta con UUID"""
        app = create_app()
        client = app.test_client()
        
        with app.app_context():
            token = create_access_token(identity='tester')

        uuid_ruta = "550e8400-e29b-41d4-a716-446655440000"
        mock_obtener.return_value = {"id": uuid_ruta, "estado": "completada"}

        response = client.get(f'/rutas/{uuid_ruta}', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == uuid_ruta
        mock_obtener.assert_called_once_with(uuid_ruta)
