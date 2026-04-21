"""Application entry point."""
import os
from app import create_app
from app.config import get_config

if __name__ == '__main__':
    config = get_config()
    app = create_app(config)
    
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )