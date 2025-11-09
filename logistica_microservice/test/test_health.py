def test_health_check(client):
    """Test del endpoint de health check"""
    response = client.get('/health')
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'healthy'
    assert json_data['service'] == 'logistica-microservice'
