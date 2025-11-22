
import pytest
from unittest.mock import MagicMock, patch
from app.services.redis_service import RedisService
import redis
import json

class TestRedisServiceUnit:
    
    @pytest.fixture
    def mock_redis(self):
        with patch('redis.Redis') as mock:
            yield mock

    @pytest.fixture
    def service(self, mock_redis):
        service = RedisService()
        app = MagicMock()
        app.config = {
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': 6379,
            'REDIS_DB': 0,
            'REDIS_PASSWORD': None,
            'CACHE_DEFAULT_TTL': 300
        }
        service.init_app(app)
        return service

    def test_init_app_error(self):
        service = RedisService()
        app = MagicMock()
        app.config = {
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': 6379,
            'REDIS_DB': 0,
            'REDIS_PASSWORD': None
        }
        
        with patch('redis.Redis', side_effect=redis.ConnectionError("Connection failed")):
            with pytest.raises(redis.ConnectionError):
                service.init_app(app)

    def test_is_available_error(self, service):
        service.client.ping.side_effect = Exception("Ping failed")
        assert service.is_available() is False
        
        service.client = None
        assert service.is_available() is False

    def test_cache_get_error(self, service):
        service.client.get.side_effect = Exception("Redis error")
        with pytest.raises(Exception) as exc:
            service.cache_get("key")
        assert "Error al obtener cache" in str(exc.value)

    def test_cache_set_error(self, service):
        service.client.setex.side_effect = Exception("Redis error")
        with pytest.raises(Exception) as exc:
            service.cache_set("key", "value")
        assert "Error al guardar en cache" in str(exc.value)

    def test_cache_delete_error(self, service):
        service.client.delete.side_effect = Exception("Redis error")
        with pytest.raises(Exception) as exc:
            service.cache_delete("key")
        assert "Error al eliminar cache" in str(exc.value)

    def test_cache_delete_pattern_error(self, service):
        service.client.scan.side_effect = Exception("Redis error")
        with pytest.raises(Exception) as exc:
            service.cache_delete_pattern("pattern:*")
        assert "Error al eliminar claves por patrón" in str(exc.value)

    def test_cache_exists_error(self, service):
        service.client.exists.side_effect = Exception("Redis error")
        with pytest.raises(Exception) as exc:
            service.cache_exists("key")
        assert "Error al verificar existencia" in str(exc.value)

    def test_cache_ttl_error(self, service):
        service.client.ttl.side_effect = Exception("Redis error")
        with pytest.raises(Exception) as exc:
            service.cache_ttl("key")
        assert "Error al obtener TTL" in str(exc.value)

    def test_cache_keys_error(self, service):
        service.client.keys.side_effect = Exception("Redis error")
        with pytest.raises(Exception) as exc:
            service.cache_keys("*")
        assert "Error al listar claves" in str(exc.value)

    def test_cache_flush_error(self, service):
        service.client.flushdb.side_effect = Exception("Redis error")
        with pytest.raises(Exception) as exc:
            service.cache_flush()
        assert "Error al limpiar cache" in str(exc.value)

    def test_queue_publish_error(self, service):
        service.client.publish.side_effect = Exception("Redis error")
        with pytest.raises(Exception) as exc:
            service.queue_publish("channel", {"msg": "test"})
        assert "Error al publicar mensaje" in str(exc.value)

    def test_queue_subscribe_error(self, service):
        service.client.pubsub.side_effect = Exception("Redis error")
        with pytest.raises(Exception) as exc:
            service.queue_subscribe(["channel"])
        assert "Error al suscribirse" in str(exc.value)

    def test_queue_channels_error(self, service):
        service.client.pubsub_channels.side_effect = Exception("Redis error")
        with pytest.raises(Exception) as exc:
            service.queue_channels("*")
        assert "Error al listar canales" in str(exc.value)

    def test_queue_num_subscribers_error(self, service):
        service.client.pubsub_numsub.side_effect = Exception("Redis error")
        with pytest.raises(Exception) as exc:
            service.queue_num_subscribers("channel")
        assert "Error al obtener subscriptores" in str(exc.value)

    def test_get_stats_error(self, service):
        service.client.info.side_effect = Exception("Redis error")
        stats = service.get_stats()
        assert stats['status'] == 'error'
        assert "Redis error" in stats['error']
