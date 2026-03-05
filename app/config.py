import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    pass


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite+pysqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    AWS_Region = 'dummy'
    COGNITO_CLIENT_ID = 'dummy'
    COGNITO_POOL_ID = 'dummy'


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:kiwirootdb@localhost:3306/kiwilocal2'
    DEBUG = True
    SQLALCHEMY_ECHO = True
    ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co"
    ALPHA_VANTAGE_API_KEY = 'R9UVMH4XA8ZPITRT'
    AWS_REGION = 'us-east-2'
    COGNITO_CLIENT_ID = 'of5ua5id9tb9oi00ibi0u7t2m'
    COGNITO_POOL_ID = 'us-east-2_pLOAUduYI'
    AWS_DOMAIN = 'kiwitestdomain'

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        f'mysql+pymysql://{os.environ.get("DB_USER", "")}:'
        f'{os.environ.get("DB_PASSWORD", "")}@'
        f'{os.environ.get("DB_HOST", "")}:'
        f'{os.environ.get("DB_PORT", "3306")}/'
        f'{os.environ.get("DB_NAME", "")}'
    )
    DEBUG = False
    SQLALCHEMY_ECHO = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'test': TestConfig,
}


def get_config(env: str):
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, DevelopmentConfig)
