
import pytest
from unittest.mock import MagicMock, patch
from app import create_app
from app.services.redis_service import redis_client

class TestRoutesUnit:
    
    @pytest.fixture
    def client(self):
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    @pytest.fixture
    def mock_redis_service(self):
        # Patch methods on the global redis_client instance
        with patch.object(redis_client, 'cache_get') as mock_get, \
             patch.object(redis_client, 'cache_set') as mock_set, \
             patch.object(redis_client, 'cache_delete') as mock_delete, \
             patch.object(redis_client, 'cache_delete_pattern') as mock_delete_pattern, \
             patch.object(redis_client, 'cache_exists') as mock_exists, \
             patch.object(redis_client, 'cache_keys') as mock_keys, \
             patch.object(redis_client, 'cache_flush') as mock_flush, \
             patch.object(redis_client, 'queue_publish') as mock_publish, \
             patch.object(redis_client, 'queue_channels') as mock_channels, \
             patch.object(redis_client, 'queue_num_subscribers') as mock_subscribers, \
             patch.object(redis_client, 'get_stats') as mock_stats, \
             patch.object(redis_client, 'cache_ttl') as mock_ttl, \
             patch.object(redis_client, 'init_app'): # Prevent real connection
            
            # Setup default return values for happy paths if needed, 
            # but we are mostly testing errors here.
            yield {
                'get': mock_get,
                'set': mock_set,
                'delete': mock_delete,
                'delete_pattern': mock_delete_pattern,
                'exists': mock_exists,
                'keys': mock_keys,
                'flush': mock_flush,
                'publish': mock_publish,
                'channels': mock_channels,
                'subscribers': mock_subscribers,
                'stats': mock_stats,
                'ttl': mock_ttl
            }

    # --- Cache Routes Errors ---

    def test_get_cache_error(self, client, mock_redis_service):
        mock_redis_service['get'].side_effect = Exception("Redis error")
        response = client.get('/api/cache/test_key')
        assert response.status_code == 500
        assert "Redis error" in response.json['error']

    def test_set_cache_error(self, client, mock_redis_service):
        mock_redis_service['set'].side_effect = Exception("Redis error")
        response = client.post('/api/cache/', json={'key': 'k', 'value': 'v'})
        assert response.status_code == 500
        assert "Redis error" in response.json['error']

    def test_delete_cache_error(self, client, mock_redis_service):
        mock_redis_service['delete'].side_effect = Exception("Redis error")
        response = client.delete('/api/cache/test_key')
        assert response.status_code == 500
        assert "Redis error" in response.json['error']

    def test_delete_cache_pattern_error(self, client, mock_redis_service):
        mock_redis_service['delete_pattern'].side_effect = Exception("Redis error")
        response = client.delete('/api/cache/pattern/test:*')
        assert response.status_code == 500
        assert "Redis error" in response.json['error']

    def test_exists_cache_error(self, client, mock_redis_service):
        mock_redis_service['exists'].side_effect = Exception("Redis error")
        response = client.get('/api/cache/exists/test_key')
        assert response.status_code == 500
        assert "Redis error" in response.json['error']

    def test_list_keys_error(self, client, mock_redis_service):
        mock_redis_service['keys'].side_effect = Exception("Redis error")
        response = client.get('/api/cache/keys')
        assert response.status_code == 500
        assert "Redis error" in response.json['error']

    def test_flush_cache_error(self, client, mock_redis_service):
        mock_redis_service['flush'].side_effect = Exception("Redis error")
        response = client.post('/api/cache/flush', json={'confirm': True})
        assert response.status_code == 500
        assert "Redis error" in response.json['error']

    # --- Queue Routes Errors ---

    def test_publish_message_error(self, client, mock_redis_service):
        mock_redis_service['publish'].side_effect = Exception("Redis error")
        response = client.post('/api/queue/publish', json={'channel': 'c', 'message': 'm'})
        assert response.status_code == 500
        assert "Redis error" in response.json['error']

    def test_list_channels_error(self, client, mock_redis_service):
        mock_redis_service['channels'].side_effect = Exception("Redis error")
        response = client.get('/api/queue/channels')
        assert response.status_code == 500
        assert "Redis error" in response.json['error']

    def test_get_subscribers_error(self, client, mock_redis_service):
        mock_redis_service['subscribers'].side_effect = Exception("Redis error")
        response = client.get('/api/queue/subscribers/test_channel')
        assert response.status_code == 500
        assert "Redis error" in response.json['error']

    # --- Health Routes Errors ---

    def test_stats_error(self, client, mock_redis_service):
        mock_redis_service['stats'].side_effect = Exception("Redis error")
        response = client.get('/stats')
        assert response.status_code == 500
        assert "Redis error" in response.json['error']

    # --- Additional Coverage for Routes ---
    
    def test_get_cache_not_found(self, client, mock_redis_service):
        mock_redis_service['get'].return_value = None
        response = client.get('/api/cache/missing_key')
        assert response.status_code == 404
        assert "Clave no encontrada" in response.json['message']

    def test_set_cache_missing_fields(self, client, mock_redis_service):
        response = client.post('/api/cache/', json={'key': 'k'}) # Missing value
        assert response.status_code == 400
        assert 'Se requieren los campos "key" y "value"' in response.json['error']

    def test_delete_cache_not_found(self, client, mock_redis_service):
        mock_redis_service['delete'].return_value = 0
        response = client.delete('/api/cache/missing_key')
        assert response.status_code == 404
        assert "Clave no encontrada" in response.json['message']

    def test_flush_cache_no_confirm(self, client, mock_redis_service):
        response = client.post('/api/cache/flush', json={})
        assert response.status_code == 400
        assert "Se requiere confirmación explícita" in response.json['error']

    def test_publish_message_missing_fields(self, client, mock_redis_service):
        response = client.post('/api/queue/publish', json={'channel': 'c'}) # Missing message
        assert response.status_code == 400
        assert 'Se requieren los campos "channel" y "message"' in response.json['error']

