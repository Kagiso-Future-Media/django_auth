from unittest.mock import patch

from django.test import TestCase
import pytest
import requests

from ... import auth_api_client
from ...exceptions import CASNetworkError, CASTimeout


class TestApiClient(TestCase):

    @patch('auth_backend.auth_api_client.requests.request', autospec=True)
    def test_call_raises_on_http_error(self, mock_request):
        mock_request.side_effect = requests.exceptions.ConnectionError

        with pytest.raises(CASNetworkError):
            auth_api_client.call('/endpoint/')

    @patch('auth_backend.auth_api_client.requests.request', autospec=True)
    def test_call_raises_on_timeout(self, mock_request):
        mock_request.side_effect = requests.exceptions.Timeout

        with pytest.raises(CASTimeout):
            auth_api_client.call('/endpoint/')
