import datetime
import logging
import sys
import uuid
from logging.handlers import RotatingFileHandler
from zoneinfo import ZoneInfo
from pydantic import ValidationError

from flask import Flask, g, jsonify, request

from flask_caching import Cache

from app.db import db
from app.log.RequestIdFilter import RequestIdFilter
from app.routes import portfolio_bp, security_bp, trade_bp, user_bp
from app.routes.domain.response_schema import ErrorResponse


cache = Cache()

def create_app(config):
    try:
        app = Flask(__name__)
        app.config.from_object(config)

        # configure and register the cache object
        app.config['CACHE_TYPE'] = 'simple'
        app.config['CACHE_DEFAULT_TIMEOUT'] = 300

        cache.init_app(app) # we register this cache object to this flask application

        # configure the logging pattern for this application
        with app.app_context():
            if app.debug or app.testing:
                handler = logging.StreamHandler(sys.stdout)
                handler.setLevel(logging.DEBUG)
            else:
                handler = RotatingFileHandler('app.log', maxBytes = 100000, backupCount = 10)
                handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter(
                '%(asctime)s %(levelname)s %(request_id)s: %(message)s (in %(module)s: %(lineno)d)'
            )
        
        @app.before_request
        def before_request():
            g.request_id = str(uuid.uuid4())
            g.start_time = datetime.datetime.now(ZoneInfo('America/New_York'))
            app.logger.info(f'New request ({g.request_id}): @{request.method} {request.host}{request.path}')

        @app.after_request
        def after_request(response):
            g.end_time = datetime.datetime.now(ZoneInfo('America/New_York'))
            duration = g.end_time - g.start_time
            app.logger.info(f'Request with ID {g.request_id} completed in {duration} seconds.')
            return response
        

        @app.errorhandler(ValidationError)
        def handle_validation_error(error):
            first_error = error.errors()[0]
            error_message = f"{first_error['loc'][0]}: {first_error['msg']}"

            response = ErrorResponse(
                error=error_message,
                request_id=getattr(g, "request_id", None)
            )

            return jsonify(response.model_dump()), 422
        
        @app.errorhandler(Exception)
        def error_handler(e):
            db.session.rollback()
            error = ErrorResponse(error_message = str(e), request_id = g.request_id)
            return jsonify(error.model_dump()), 500
        

            
        # register extensions
        db.init_app(app)

        # register blueprints
        app.register_blueprint(user_bp, url_prefix='/users')
        app.register_blueprint(portfolio_bp, url_prefix='/portfolios')
        app.register_blueprint(security_bp, url_prefix='/securities')
        app.register_blueprint(trade_bp, url_prefix='/trades')

        return app
    except Exception as e:
        print(f'Error creating app: {e}')
        raise
