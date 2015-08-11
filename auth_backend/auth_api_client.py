import json
import logging

import requests

from . import settings
from .exceptions import CASNetworkError, CASTimeout

logger = logging.getLogger('django')

AUTH_HEADERS = {
    'AUTHORIZATION': 'Token {0}'.format(settings.CAS_TOKEN),
    'SOURCE-ID': settings.CAS_SOURCE_ID,
}
BASE_URL = settings.CAS_BASE_URL
TIMEOUT_IN_SECONDS = 3


def call(endpoint, method='GET', payload=None):
    url = '{base_url}/{endpoint}/.json'.format(
        base_url=BASE_URL,
        endpoint=endpoint
    )

    try:
        response = requests.request(
            method,
            url,
            headers=AUTH_HEADERS,
            json=payload,
            timeout=TIMEOUT_IN_SECONDS
        )
    except requests.exceptions.ConnectionError as e:
        raise CASNetworkError from e
    except requests.exceptions.Timeout as e:
        raise CASTimeout from e

    logger.debug('method={0}'.format(method))
    logger.debug('url={0}'.format(url))
    logger.debug('headers={0}'.format(AUTH_HEADERS))
    logger.debug('payload={0}'.format(payload))
    logger.debug('json={0}'.format(json.dumps(payload)))

    json_data = {}
    try:
        json_data = response.json()
    except ValueError:
        # Requests chokes on empty body
        pass

    return response.status_code, json_data
