import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-pro-latest')
    MAX_CHAT_HISTORY = 10
    MAX_MESSAGE_LENGTH = 5000
    CHAT_TIMEOUT = 60  # Increased from 30 to 60 seconds
    CORS_ORIGINS = ["http://localhost:5000", "http://127.0.0.1:5000"]

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    CORS_ORIGINS = ["*"]  # Allow all in dev

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5000').split(',')

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
