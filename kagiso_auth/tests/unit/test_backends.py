from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
import pytest
import responses

from . import mocks
from ... import http
from ...backends import KagisoBackend
from ...exceptions import AuthAPIUnexpectedStatusCode, EmailNotConfirmedError
from ...models import KagisoUser


class KagisoBackendTest(TestCase):

    @responses.activate
    @patch('kagiso_auth.backends.KagisoUser', autospec=True)
    def test_authenticate_valid_credentials_returns_user(self, MockKagisoUser):  # noqa
        email = 'test@email.com'
        password = 'random'
        user = KagisoUser(email=email, password=password)

        MockKagisoUser.sync_user_data_locally.return_value = user

        url, _ = mocks.post_sessions(
            http.HTTP_200_OK,
            last_sign_in_via=settings.APP_NAME
        )

        backend = KagisoBackend()
        result = backend.authenticate(
            email=email,
            password=password,
        )

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == url

        assert isinstance(result, KagisoUser)
        assert result.id == user.id

    @responses.activate
    def test_authenticate_valid_credentials_creates_local_user_if_none(self):
        email = 'test@email.com'
        password = 'random'

        data = {
            'id': 55,
            'email': email,
            'first_name': 'Fred',
            'last_name': 'Smith',
            'is_staff': True,
            'is_superuser': True,
            'profile': {'age': 40, },
            'created_via': settings.APP_NAME,
            'last_sign_in_via': settings.APP_NAME
        }

        session_url, data = mocks.post_sessions(
            http.HTTP_200_OK,
            **data
        )

        backend = KagisoBackend()
        result = backend.authenticate(
            email=email,
            password=password,
        )

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == session_url

        assert result.email == data['email']

    @responses.activate
    def test_authenticate_invalid_status_code_raises(self):
        email = 'test@email.com'
        password = 'random'
        url, api_data = mocks.post_users(1, email)
        KagisoUser.objects.create_user(email, password)

        mocks.post_sessions(500)

        backend = KagisoBackend()

        with pytest.raises(AuthAPIUnexpectedStatusCode):
            backend.authenticate(
                email=email,
                password=password,
            )

    @responses.activate
    @patch('kagiso_auth.backends.KagisoUser', autospec=True)
    def test_authenticate_with_social_sign_in_returns_user(self, MockKagisoUser):  # noqa
        email = 'test@email.com'
        password = 'secret'
        strategy = 'facebook'
        user = KagisoUser(email=email, password=password)

        MockKagisoUser.sync_user_data_locally.return_value = user

        url, data = mocks.post_sessions(http.HTTP_200_OK)
        mocks.put_users(1, email)

        backend = KagisoBackend()
        result = backend.authenticate(
            email=email,
            strategy=strategy,
        )

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == url

        assert isinstance(result, KagisoUser)
        assert result.id == user.id

    @responses.activate
    def test_authenticate_invalid_credentials_returns_none(self):
        email = 'test@email.com'
        password = 'incorrect'
        mocks.post_users(1, email)
        KagisoUser.objects.create_user(email, password)
        url, data = mocks.post_sessions(http.HTTP_404_NOT_FOUND)

        backend = KagisoBackend()
        result = backend.authenticate(email=email, password=password)

        assert len(responses.calls) == 2
        assert responses.calls[1].request.url == url

        assert not result

    @responses.activate
    def test_authenticate_unconfirmed_email_raises(self):
        email = 'test@email.com'
        password = 'random'
        url, api_data = mocks.post_users(1, email)
        KagisoUser.objects.create_user(email, password)

        mocks.post_sessions(http.HTTP_422_UNPROCESSABLE_ENTITY)

        backend = KagisoBackend()

        with pytest.raises(EmailNotConfirmedError):
            backend.authenticate(email=email, password=password)
