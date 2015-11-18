import json
import logging

import requests

from . import settings
from .exceptions import AuthAPINetworkError, AuthAPITimeout


logger = logging.getLogger('django')


class AuthApiClient:

    BASE_URL = settings.AUTH_API_BASE_URL
    TIMEOUT_IN_SECONDS = 6

    def __init__(self):
        self._auth_api_token = settings.AUTH_API_TOKEN

    def call(self, endpoint, method='GET', payload=None):
        auth_headers = {
            'AUTHORIZATION': 'Token {0}'.format(self._auth_api_token),
        }
        url = '{base_url}/{endpoint}/.json'.format(
            base_url=self.BASE_URL,
            endpoint=endpoint
        )

        try:
            response = requests.request(
                method,
                url,
                headers=auth_headers,
                json=payload,
                timeout=self.TIMEOUT_IN_SECONDS
            )
        except requests.exceptions.ConnectionError as e:
            raise AuthAPINetworkError from e
        except requests.exceptions.Timeout as e:
            raise AuthAPITimeout from e

        logger.debug('method={0}'.format(method))
        logger.debug('url={0}'.format(url))
        logger.debug('headers={0}'.format(auth_headers))
        logger.debug('payload={0}'.format(payload))
        logger.debug('json={0}'.format(json.dumps(payload)))

        json_data = {}
        try:
            json_data = response.json()
        except ValueError:
            # Requests chokes on empty body
            pass

        return response.status_code, json_data
