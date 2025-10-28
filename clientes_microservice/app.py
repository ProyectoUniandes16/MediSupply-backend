import os
from src import create_app
from src.config.config import Config

# Crear la aplicación usando la factory function
app = create_app(Config)

if __name__ == '__main__':
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=5010, debug=debug)
