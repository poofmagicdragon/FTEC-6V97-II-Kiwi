import requests
import json

from flask import current_app
class CognitoClientError(Exception):
    pass

def get_user_info(access_token: str):
    try:    
        current_app.logger.debug('Fetching user info from Cognito')
        region = current_app.config.get('AWS_REGION')
        url = f'https://cognito-idp.{region}.amazonaws.com/'
        headers = {
            'Content-Type': 'application/x-amz-json-1.1',
            'X-Amz-Target': 'AWSCognitoIdentityProviderService.GetUser'
        }
        body = {'AccessToken': access_token}
        response = requests.post(url, headers = headers, data = json.dumps(body))
        response.raise_for_status()
        data = response.json()
        # {}'UserAttributes'}
        attributes = {attr['Name']: attr['Value'] for attr in data['UserAttributes']}
        username = data['Username']
        current_app.logger.debug('Successfully fetched user info from access token')
        return {'username':username, 'attributes': attributes}
    except Exception as e:
        current_app.logger.debug(f'Error fetching user info from token: {str(e)}')
        raise CognitoClientError(f'Failed to get user info from user token. Error: {str(e)}')