import requests
import json


from flask import current_app
class CognitoClientError(Exception):
    pass

def get_user_info(access_token: str):
    try:
        current_app.logger.debug('Fetching user info from Cognito')

        region = current_app.config.get('AWS_REGION')
        domain = current_app.config.get('AWS_DOMAIN')

        url = f"https://{domain}.auth.{region}.amazoncognito.com/oauth2/userInfo"

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()

        username = data.get("username") or data.get("preferred_username") or data.get("sub")
        attributes = data

        return {"username": username, "attributes": attributes}

    except Exception as e:
        current_app.logger.debug(f"Error fetching user info from token: {str(e)}")
        raise CognitoClientError(f"Failed to get user info from user token. Error: {str(e)}")

    
