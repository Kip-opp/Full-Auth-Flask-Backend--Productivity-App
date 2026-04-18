from flask import Flask, jsonify, render_template
from app.config import Config
from app.extensions import db, migrate, jwt, bcrypt
from app.routes.auth import auth_bp
from app.routes.todos import todos_bp


def create_app():
    app = Flask(
        __name__,
        template_folder="../frontend/templates",
        static_folder="../frontend/static",
        static_url_path="/static",
    )

    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(todos_bp, url_prefix="/api/todos")

    @app.get("/api/health")
    def health():
        return jsonify({"message": "API is running"}), 200

    return app
