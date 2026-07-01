"""
FitPro AI - Configuration Module
================================
Centralized configuration for Flask application.
Supports multiple environments: development, testing, production.
"""

import os
from datetime import timedelta

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration with common settings."""

    # Flask Core
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fitpro-ai-super-secret-key-2024-change-in-production'
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File Uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Database - SQLite (default for easy setup)
    # Change DB_TYPE to 'mysql' for MySQL connection
    DB_TYPE = os.environ.get('DB_TYPE') or 'sqlite'
    
    # SQLite Configuration
    SQLITE_DB_PATH = os.path.join(BASE_DIR, 'fitpro.db')
    
    # MySQL Configuration (used when DB_TYPE='mysql')
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'fitpro_user'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'fitpro_pass'
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'fitpro'
    
    # AI / OpenAI
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or ''
    
    # App Settings
    APP_NAME = 'FitPro AI'
    APP_VERSION = '1.0.0'
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Must be set in production
    
    # Use MySQL in production
    DB_TYPE = os.environ.get('DB_TYPE') or 'mysql'


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    DEBUG = True
    DB_TYPE = 'sqlite'
    SQLITE_DB_PATH = ':memory:'
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on FLASK_ENV environment variable."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)()
