"""
Application configuration management.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'notes_app.db')


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 168))
    JWT_EXPIRATION_DELTA = timedelta(hours=JWT_EXPIRATION_HOURS)
    
    ITEMS_PER_PAGE = 10
    MAX_ITEMS_PER_PAGE = 100
    
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5500,http://localhost:5173,http://localhost:8000,http://127.0.0.1:5500').split(',')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        f'sqlite:///{DB_PATH}'
    )


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'test-jwt-secret-key'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')


def get_config():
    """Get configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    config_map = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig,
    }
    return config_map.get(env, DevelopmentConfig)
