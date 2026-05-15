import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    pass



class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite+pysqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    AWS_REGION = 'dummy'
    COGNITO_CLIENT_ID = 'dummy'
    COGNITO_POOL_ID = 'dummy'
    ALPHA_VANTAGE_API_KEY = ''


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'insert here'
    DEBUG = True
    SQLALCHEMY_ECHO = True
    ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co"
    ALPHA_VANTAGE_API_KEY = 'insert here'
    AWS_REGION = 'insert here'
    COGNITO_CLIENT_ID = 'insert here'
    COGNITO_POOL_ID = 'insert here'
    AWS_DOMAIN = 'insert here'
    

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
