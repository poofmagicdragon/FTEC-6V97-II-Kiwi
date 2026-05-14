from functools import wraps
from typing import Dict
from flask import request, g, jsonify, current_app
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
import requests

from app.service import user_service
from app.service.cognito_client import get_user_info
from app.db import db

from app.common.response_schema import ErrorResponse

#Authorization 

class CognitoTokenValidator:
    def __init__(self, region: str, user_pool_id: str, client_id: str):
        self.region = region
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        self._jwks_url = f'{self.issuer}/.well-known/jwks.json'
        self._jwks = None

    def _get_jwks(self) -> Dict:
        '''
        Get the public keys that are associated with the user pool.  These will be used everytime to verify the token signature
        '''
        if self._jwks is None:
            response = requests.get(self._jwks_url)
            response.raise_for_status()
            self._jwks = response.json()
        return self._jwks 

    def _get_signing_key(self, token: str):
        '''
        Extract the signing key from the token
        '''
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')
            if not kid:
                return None
            # find the matching key from the jwks for the given key id
            jwks = self._get_jwks()
            for key in self._jwks.get("keys", []):
                if key.get('kid') == kid:
                    return key
            return None
        except JWTError:
            return None

    def validate_token(self, token: str):
        signing_key = self._get_signing_key(token)
        if not signing_key:
            raise Exception('Unable to find a matching signing key')
        
        try:
            claims = jwt.decode(
                token,
                signing_key,
                algorithms = ['RS256'],
                audience=self.client_id,
                issuer = self.issuer,
                options = {
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_aud': True,
                    'verify_iss': True
                }
            )

            if claims.get('token_use') != 'access':
                raise Exception(f'Invalid token use: {claims.get('token_use')}')
            
            return claims
        
        except ExpiredSignatureError as e:
            raise Exception('Token has expired')
        except JWTClaimsError as e:
            raise Exception(f'Invalid token claims: {str(e)}')
        except JWTError as e:
            raise Exception(f"Token validation failed: {str(e)}")
        
def get_token_from_header():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) !=2 or parts[0].lower() != 'bearer':
        return None
    return parts[1]


# Authentication
def required_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        if not token:
            return jsonify(ErrorResponse(error_message = 'Missing authentication Token', request_id = '').model_dump()), 403
        
        validator = current_app.config.get('COGNITO_VALIDATOR')

        if not validator:
            return jsonify(ErrorResponse(error_message = 'Missing cognito token validator in the app configuration', request_id = '').model_dump()), 403
        
        try:
            from app import cache
            claims = validator.validate_token(token)
            g.user = {
                'user_id': claims.get('sub'),
                'username': claims.get('username'),
                'claims': claims

            }

            if cache.get('pre_request_all_users') is None:
                users = user_service.get_all_users()
                cache.set('pre_request_all_users', users, timeout = 60)
            users = cache.get('pre_request_all_users')
            caller_username = g.user['username']
            caller_user = next((u for u in users if u.username == caller_username), None)
            try:
                if not caller_user: # create the user in the database
                    token = get_token_from_header()
                    if token is None:
                        return jsonify(ErrorResponse(error_message = 'Failed to get info user from token: token does not exist', request_id = g.request_id).model_dump()), 403
                    
                    user_info = get_user_info(token)
                    username = user_info.get('username')
                    firstname = user_info.get('attributes', {}).get('given_name')
                    lastname = user_info.get('attributes', {}).get('family_name')
                    
                    user_service.create_user(username, firstname, lastname, 1000.00)
                    db.session.commit()
                    
                    users = user_service.get_all_users()
                    cache.set('pre_request_all_users', users, timeout = 60)
            except Exception as e:
                error_msg = f'Failed to add user in the database for a new user: {str(e)}'
                current_app.logger.error(error_msg)
                return jsonify(ErrorResponse(error_message = error_msg, request_id = g.request_id).model_dump()), 500
            


        except Exception as e:
            return jsonify(ErrorResponse(error_message = f'Token validation failed: {str(e)}', request_id = '').model_dump()), 403
        
        # This line will not be reached if any of the exceptions above happened
        return f(*args, **kwargs)

    return decorated_function

        
