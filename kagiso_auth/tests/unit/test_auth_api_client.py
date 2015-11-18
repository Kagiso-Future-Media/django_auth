from unittest.mock import patch

from django.test import TestCase
import pytest
import requests

from ...auth_api_client import AuthApiClient
from ...exceptions import AuthAPINetworkError, AuthAPITimeout


class TestApiClient(TestCase):

    @patch('kagiso_auth.auth_api_client.requests.request', autospec=True)
    def test_call_raises_on_http_error(self, mock_request):
        auth_api_client = AuthApiClient()
        mock_request.side_effect = requests.exceptions.ConnectionError

        with pytest.raises(AuthAPINetworkError):
            auth_api_client.call('/endpoint/')

    @patch('kagiso_auth.auth_api_client.requests.request', autospec=True)
    def test_call_raises_on_timeout(self, mock_request):
        auth_api_client = AuthApiClient()
        mock_request.side_effect = requests.exceptions.Timeout

        with pytest.raises(AuthAPITimeout):
            auth_api_client.call('/endpoint/')
