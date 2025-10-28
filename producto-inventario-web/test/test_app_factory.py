from src import create_app


def test_app_initialization_and_health():
    app = create_app()
    app.config['TESTING'] = True

    assert {'health', 'producto', 'inventarios'}.issubset(app.blueprints)

    with app.test_client() as client:
        response = client.get('/health')
        assert response.status_code == 200
        assert response.data == b'OK'
