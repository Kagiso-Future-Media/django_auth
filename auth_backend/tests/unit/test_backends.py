from django.test import TestCase
import pytest
import responses

from . import mocks
from ...backends import KagisoBackend
from ...exceptions import CASUnexpectedStatusCode, EmailNotConfirmedError
from ...models import KagisoUser


class KagisoBackendTest(TestCase):

    @responses.activate
    def test_authenticate_valid_credentials_returns_user(self):
        email = 'test@email.com'
        password = 'random'
        profile = {
            'first_name': 'Fred'
        }
        mocks.mock_out_post_users(
            1,
            email,
            profile=profile
        )
        user = KagisoUser.objects.create_user(
            email, password, profile=profile)
        url, _ = mocks.mock_out_post_sessions(200)

        backend = KagisoBackend()
        result = backend.authenticate(email=email, password=password)

        assert len(responses.calls) == 2
        assert responses.calls[1].request.url == url

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
        }

        _, api_data = mocks.mock_out_post_users(1, email)
        session_url, data = mocks.mock_out_post_sessions(200, **data)

        backend = KagisoBackend()
        result = backend.authenticate(email=email, password=password)

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == session_url

        assert result.id == data['id']
        assert result.email == data['email']
        assert result.first_name == data['first_name']
        assert result.last_name == data['last_name']
        assert result.is_staff == data['is_staff']
        assert result.is_superuser == data['is_superuser']
        assert result.profile == data['profile']

    @responses.activate
    def test_authenticate_invalid_status_code_raises(self):
        email = 'test@email.com'
        password = 'random'
        url, api_data = mocks.mock_out_post_users(1, email)
        KagisoUser.objects.create_user(email, password)

        mocks.mock_out_post_sessions(500)

        backend = KagisoBackend()

        with pytest.raises(CASUnexpectedStatusCode):
            backend.authenticate(email=email, password=password)

    @responses.activate
    def test_authenticate_with_social_sign_in_returns_user(self):
        email = 'test@email.com'
        strategy = 'facebook'
        mocks.mock_out_post_users(1, email)
        # Unusable password is saved locally for Django compliance
        # It is not used for auth purposes though
        user = KagisoUser.objects.create_user(email, password='unusable')
        url, data = mocks.mock_out_post_sessions(200)

        backend = KagisoBackend()
        result = backend.authenticate(email=email, strategy=strategy)

        assert len(responses.calls) == 2
        assert responses.calls[1].request.url == url

        assert isinstance(result, KagisoUser)
        assert result.id == user.id

    @responses.activate
    def test_authenticate_invalid_credentials_returns_none(self):
        email = 'test@email.com'
        password = 'incorrect'
        mocks.mock_out_post_users(1, email)
        KagisoUser.objects.create_user(email, password)
        url, data = mocks.mock_out_post_sessions(404)

        backend = KagisoBackend()
        result = backend.authenticate(email=email, password=password)

        assert len(responses.calls) == 2
        assert responses.calls[1].request.url == url

        assert not result

    @responses.activate
    def test_authenticate_unconfirmed_email_raises(self):
        email = 'test@email.com'
        password = 'random'
        url, api_data = mocks.mock_out_post_users(1, email)
        KagisoUser.objects.create_user(email, password)

        mocks.mock_out_post_sessions(422)

        backend = KagisoBackend()

        with pytest.raises(EmailNotConfirmedError):
            backend.authenticate(email=email, password=password)
