from flask import Flask, jsonify
from app.config import Config
from app.extensions import db, migrate, jwt, bcrypt
from app.routes.auth import auth_bp
from app.routes.todos import todos_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(todos_bp, url_prefix="/api/todos")

    @app.get("/")
    def home():
        return jsonify({
            "message": "AI Todo Backend is running",
            "status": "ok"
        })

    return app