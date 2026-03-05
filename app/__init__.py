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
from app.common.response_schema import ErrorResponse
from app.auth import CognitoTokenValidator
#from app.config import get_config


cache = Cache()

def create_app(config):  #  = get_config("development")
    try:
        app = Flask(__name__)
        app.config.from_object(config)

        # configure and register the cache object
        app.config['CACHE_TYPE'] = 'simple'
        app.config['CACHE_DEFAULT_TIMEOUT'] = 300
        
        # cognito  config
        #app.config['COGNITO_Validator'] = CognitoTokenValidator(region = 'us-east-2', user_pool_id = "us-east-2_nvcA2OL9j", client_id = "7o1cnmbvg5t8bh295q2igp7buk", domain = "kiwidomain")

        # configure the token validator
        token_validator = CognitoTokenValidator(app.config['AWS_REGION'], app.config['COGNITO_POOL_ID'], app.config['COGNITO_CLIENT_ID'])

        app.config['COGNITO_VALIDATOR'] = token_validator

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
        # check whether the incoming user is already created in the DB
        # if it is then there is nothing to do -> Proceed with the request
        # otherwise, create new record for this user in the database (default the balance to 1000) -> Proceed with the request

        # optimization: in order to prevent a database call on every request we will query all users from the db and store in cache
        # first we look up the username in the cache if it exists then the user exists in the user table -> proceed with the request
        # else this is a new user: 1) create the user 2) query all users again to update cache -> proceed with request
            # if cache.get('pre_request_all_users') is None:
            #     users = user_service.get_all_users()
            #     cache.set('pre_request_all_users', users, timeout = 60)
            # users = cache.get('pre_request_all_users')
            # caller_username = g.user['username']
            # caller_user = next((u for u in users if u.username == caller_username), None)
            # try:
            #     if not caller_user: # create the user in the database
            #         token = auth.get_token_from_header()
            #         if token is None:
            #             return jsonify(ErrorResponse(error_message = 'Failed to get info user from token: token does not exist', request_id = g.request_id).model_dump()), 400
                    
            #         user_info = get_user_info(token)
            #         username = user_info.get('username')
            #         firstname = user_info.get('attributes', {}).get('given_name')
            #         lastname = user_info.get('attributes', {}).get('family_name')
                    
            #         user_service.create_user(username, firstname, lastname, 1000.00)
            #         db.session.commit()
                    
            #         users = user_service.get_all_users()
            #         cache.set('pre_request_all_users', users, timeout = 60)
            # except Exception as e:
            #     error_msg = f'Failed to add user in the database for a new user'
            #     app.logger.error(error_msg)
            #     return jsonify(ErrorResponse(error_message = error_msg, request_id = g.request_id)), 500


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
                error_message=error_message,
                request_id=getattr(g, "request_id", None)
            )

            return jsonify(response.model_dump()), 422
        
        @app.errorhandler(Exception)
        def error_handler(e):
            db.session.rollback()
            print("ERROR:", repr(e))
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
