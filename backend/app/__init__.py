"""Flask application factory."""
from flask import Flask
from flask_cors import CORS
from app.extensions import db, migrate, bcrypt
from app.config import get_config


def create_app(config=None):
    """Create and configure Flask application."""
    app = Flask(__name__)

    if config is None:
        config = get_config()
    app.config.from_object(config)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    
    # CORS configuration
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', ['http://localhost:3000']),
            "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    from app.routes import (
        auth_bp,
        notes_bp,
        workspaces_bp,
        sources_bp,
        artifacts_bp,
        jobs_bp,
        workspace_notes_bp,
        queries_bp,
    )
    app.register_blueprint(auth_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(workspaces_bp)
    app.register_blueprint(sources_bp)
    app.register_blueprint(artifacts_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(workspace_notes_bp)
    app.register_blueprint(queries_bp)

    from app.cli import register_cli
    register_cli(app)

    @app.route('/api/health', methods=['GET'])
    def health():
        return {'status': 'ok'}, 200

    return app