import json
import logging

import requests

from . import settings
from .exceptions import AuthAPINetworkError, AuthAPITimeout


logger = logging.getLogger('django')


class AuthApiClient:

    BASE_URL = settings.AUTH_API_BASE_URL
    TIMEOUT_IN_SECONDS = 6
    AUTH_API_TOKEN = settings.AUTH_API_TOKEN

    @classmethod
    def call(cls, endpoint, method='GET', payload=None):
        auth_headers = {
            'AUTHORIZATION': 'Token {0}'.format(cls.AUTH_API_TOKEN),
        }
        url = '{base_url}/{endpoint}/.json'.format(
            base_url=cls.BASE_URL,
            endpoint=endpoint
        )

        try:
            response = requests.request(
                method,
                url,
                headers=auth_headers,
                json=payload,
                timeout=cls.TIMEOUT_IN_SECONDS
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
