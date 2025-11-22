import pytest
from unittest.mock import MagicMock, patch
from app.services.redis_queue_service import RedisQueueService

class TestRedisQueueService:

    @pytest.fixture(autouse=True)
    def disable_queue(self):
        """Override the global disable_queue fixture to allow real calls in this test suite."""
        yield

    def test_get_redis_url(self, app):
        with app.app_context():
            url = RedisQueueService._get_redis_url()
            assert url == 'http://redis-service.test'

    @patch('app.services.redis_queue_service.requests.post')
    def test_enqueue_cache_update_success(self, mock_post, app):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'subscribers': 1}
        mock_post.return_value = mock_response

        with app.app_context():
            result = RedisQueueService.enqueue_cache_update('prod-1', 'create', {'foo': 'bar'})
            
        assert result is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs['json']['message']['productoId'] == 'prod-1'
        assert kwargs['json']['message']['action'] == 'create'

    @patch('app.services.redis_queue_service.requests.post')
    def test_enqueue_cache_update_failure_status(self, mock_post, app):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        with app.app_context():
            result = RedisQueueService.enqueue_cache_update('prod-1', 'create')
            
        assert result is False

    @patch('app.services.redis_queue_service.requests.post')
    def test_enqueue_cache_update_request_exception(self, mock_post, app):
        mock_post.side_effect = Exception("Connection error")

        with app.app_context():
            result = RedisQueueService.enqueue_cache_update('prod-1', 'create')
            
        assert result is False

    @patch('app.services.redis_queue_service.requests.get')
    def test_check_health_success(self, mock_get, app):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with app.app_context():
            result = RedisQueueService.check_health()
            
        assert result is True

    @patch('app.services.redis_queue_service.requests.get')
    def test_check_health_failure(self, mock_get, app):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        with app.app_context():
            result = RedisQueueService.check_health()
            
        assert result is False

    @patch('app.services.redis_queue_service.requests.get')
    def test_check_health_exception(self, mock_get, app):
        mock_get.side_effect = Exception("Connection error")

        with app.app_context():
            result = RedisQueueService.check_health()
            
        assert result is False
