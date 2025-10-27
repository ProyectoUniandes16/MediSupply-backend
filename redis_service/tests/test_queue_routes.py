"""
Tests de integración para las rutas de queue (Pub/Sub) del Redis Service
"""
import pytest
import json


@pytest.mark.integration
class TestQueueRoutes:
    """Tests para las rutas de queue (Pub/Sub)."""
    
    def test_queue_publish(self, client):
        """Test de publicar mensaje en cola."""
        data = {
            "channel": "test_channel",
            "message": {"action": "test", "data": "test_data"}
        }
        response = client.post(
            '/api/queue/publish',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        result = response.get_json()
        assert 'subscribers' in result
        assert result['channel'] == 'test_channel'
    
    def test_queue_publish_invalid_data(self, client):
        """Test de publicar sin datos requeridos."""
        # Sin channel
        response = client.post(
            '/api/queue/publish',
            data=json.dumps({"message": "test"}),
            content_type='application/json'
        )
        assert response.status_code == 400
        
        # Sin message
        response = client.post(
            '/api/queue/publish',
            data=json.dumps({"channel": "test"}),
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_queue_channels(self, client):
        """Test de obtener lista de canales."""
        response = client.get('/api/queue/channels')
        
        assert response.status_code == 200
        result = response.get_json()
        assert 'channels' in result
        assert isinstance(result['channels'], list)
    
    def test_queue_subscribers(self, client):
        """Test de obtener número de suscriptores."""
        response = client.get('/api/queue/subscribers/test_channel')
        
        assert response.status_code == 200
        result = response.get_json()
        assert 'channel' in result
        assert 'subscribers' in result
        assert result['channel'] == 'test_channel'
        assert isinstance(result['subscribers'], int)
