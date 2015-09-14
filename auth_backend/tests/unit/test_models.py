from dateutil import parser
from django.db.utils import IntegrityError
from django.test import TestCase
from model_mommy import mommy
import pytest
import responses

from . import mocks
from ... import models
from ...exceptions import CASUnexpectedStatusCode


class KagisoUserTest(TestCase):

    @responses.activate
    def test_create(self):
        # ------------------------
        # -------Arrange----------
        # ------------------------

        email = 'test@email.com'
        first_name = 'Fred'
        last_name = 'Smith'
        is_staff = True
        is_superuser = True
        profile = {
            'age': 22
        }

        url, api_data = mocks.mock_out_post_users(
            1,
            email,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_superuser=is_superuser,
            profile=profile
        )
        # ------------------------
        # -------Act--------------
        # ------------------------

        user = mommy.make(
            models.KagisoUser,
            id=None,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_superuser=is_superuser,
            profile=profile,
        )

        # ------------------------
        # -------Assert----------
        # ------------------------

        # Confirmation tokens are saved in memory only.
        assert user.confirmation_token == api_data['confirmation_token']

        result = models.KagisoUser.objects.get(id=user.id)

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == url

        assert result.id == api_data['id']
        assert result.email == api_data['email']
        assert result.first_name == api_data['first_name']
        assert result.last_name == api_data['last_name']
        assert result.is_staff == api_data['is_staff']
        assert result.is_superuser == api_data['is_superuser']
        assert not result.email_confirmed
        assert result.confirmation_token is None
        assert result.profile == api_data['profile']
        assert result.date_joined == parser.parse(api_data['created'])
        assert result.modified == parser.parse(api_data['modified'])

    @responses.activate
    def test_create_raises_if_user_exists_on_cas(self):
        email = 'test@email.com'
        data = {
            'first_name': 'Fred',
            'last_name': 'Smith',
            'is_staff': True,
            'is_superuser': True,
            'profile': {
                'age': 22,
            }
        }

        url, api_data = mocks.mock_out_post_users(
            1,
            email,
            status=409,
            **data
        )

        with pytest.raises(IntegrityError):
            mommy.make(
                models.KagisoUser,
                id=None,
                email=email,
            )

    @responses.activate
    def test_create_invalid_status_code_raises(self):
        email = 'test@email.com'
        mocks.mock_out_post_users(1, email, status=500)

        with pytest.raises(CASUnexpectedStatusCode):
            mommy.make(
                models.KagisoUser,
                id=None,
                email=email,
            )

    @responses.activate
    def test_update(self):
        # ------------------------
        # -------Arrange----------
        # ------------------------
        mocks.mock_out_post_users(1, 'test@email.com')

        user = mommy.make(models.KagisoUser, id=None)

        email = 'test@email.com'
        first_name = 'Fred'
        last_name = 'Smith'
        is_staff = True
        is_superuser = True
        profile = {
            'age': 22
        }

        url, api_data = mocks.mock_out_put_users(
            1,
            email,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_superuser=is_superuser,
            profile=profile
        )

        # ------------------------
        # -------Act--------------
        # ------------------------

        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.profile = profile
        user.save()

        # ------------------------
        # -------Assert----------
        # ------------------------
        result = models.KagisoUser.objects.get(id=user.id)

        assert len(responses.calls) == 2
        assert responses.calls[1].request.url == url

        assert result.id == api_data['id']
        assert result.email == api_data['email']
        assert result.first_name == api_data['first_name']
        assert result.last_name == api_data['last_name']
        assert result.is_staff == api_data['is_staff']
        assert result.is_superuser == api_data['is_superuser']
        assert result.profile == api_data['profile']
        assert result.modified == parser.parse(api_data['modified'])

    @responses.activate
    def test_update_syncs_if_user_doesnt_exist_on_cas(self):
        # ------------------------
        # -------Arrange----------
        # ------------------------
        post_url, _ = mocks.mock_out_post_users(1, 'test@email.com')

        user = mommy.make(models.KagisoUser, id=None)

        email = 'test@email.com'
        data = {
            'first_name': 'Fred',
            'last_name': 'Smith',
            'is_staff': True,
            'is_superuser': True,
            'profile': {
                'age': 22,
            }
        }

        put_url, api_data = mocks.mock_out_put_users(
            1,
            email,
            status=404,
        )
        post_url, _ = mocks.mock_out_post_users(2, 'test@email.com', **data)

        # ------------------------
        # -------Act--------------
        # ------------------------

        user.email = email
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.is_staff = data['is_staff']
        user.is_superuser = data['is_superuser']
        user.profile = data['profile']
        user.save()

        # ------------------------
        # -------Assert----------
        # ------------------------
        result = models.KagisoUser.objects.get(id=user.id)

        assert len(responses.calls) == 3
        last_api_call = responses.calls[-1].request
        assert last_api_call.method == 'POST'

        assert result.id == api_data['id']
        assert result.email == api_data['email']
        assert result.first_name == api_data['first_name']
        assert result.last_name == api_data['last_name']
        assert result.is_staff == api_data['is_staff']
        assert result.is_superuser == api_data['is_superuser']
        assert result.profile == api_data['profile']
        assert result.modified == parser.parse(api_data['modified'])

    @responses.activate
    def test_update_invalid_status_code_raises(self):
        mocks.mock_out_post_users(1, 'test@email.com')
        user = mommy.make(models.KagisoUser, id=None)
        email = 'test@email.com'
        url, api_data = mocks.mock_out_put_users(1, email, status=500)

        user.email = email

        with pytest.raises(CASUnexpectedStatusCode):
            user.save()

    @responses.activate
    def test_delete(self):
        mocks.mock_out_post_users(1, 'test@email.com')
        user = mommy.make(models.KagisoUser, id=None)
        url = mocks.mock_out_delete_users(user.id)

        user.delete()

        user_deleted = not models.KagisoUser.objects.filter(
            id=user.id).exists()

        assert len(responses.calls) == 2
        assert responses.calls[1].request.url == url

        assert user_deleted

    @responses.activate
    def test_delete_invalid_status_code_raises(self):
        mocks.mock_out_post_users(1, 'test@email.com')
        user = mommy.make(models.KagisoUser, id=None)
        mocks.mock_out_delete_users(user.id, status=500)

        with pytest.raises(CASUnexpectedStatusCode):
            user.delete()

    def test_get_full_name_returns_email(self):
        email = 'test@email.com'
        user = models.KagisoUser(email=email)

        assert user.get_full_name() == email

    def test_get_short_name_returns_email(self):
        email = 'test@email.com'
        user = models.KagisoUser(email=email)

        assert user.get_short_name() == email

    def test_set_password(self):
        user = models.KagisoUser()
        password = 'my_password'

        user.set_password(password)

        assert user.raw_password == password

    def test_get_username_returns_email(self):
        email = 'test@email.com'
        user = models.KagisoUser(email=email)

        assert user.username == email

    def test_set_username_sets_username(self):
        username = 'test@username.com'
        user = models.KagisoUser(username=username)

        assert user.email == username

    @responses.activate
    def test_confirm_email(self):
        _, post_data = mocks.mock_out_post_users(1, 'test@email.com')
        user = mommy.make(models.KagisoUser, id=None)
        mocks.mock_out_put_users(
            user.id,
            user.email,
            profile=user.profile
        )
        url = mocks.mock_out_post_confirm_email()

        user.confirm_email(post_data['confirmation_token'])

        assert len(responses.calls) == 3
        # Create user, confirm user, update user...
        assert responses.calls[1].request.url == url

        result = models.KagisoUser.objects.get(id=user.id)

        assert result.email_confirmed
        assert not result.confirmation_token

    @responses.activate
    def test_confirm_email_invalid_status_code_raises(self):
        _, post_data = mocks.mock_out_post_users(1, 'test@email.com')
        user = mommy.make(models.KagisoUser, id=None)
        mocks.mock_out_put_users(
            user.id,
            user.email,
            profile=user.profile
        )
        mocks.mock_out_post_confirm_email(status=500)

        with pytest.raises(CASUnexpectedStatusCode):
            user.confirm_email(post_data['confirmation_token'])

        assert not user.email_confirmed

    @responses.activate
    def test_record_sign_out(self):
        id = 1
        _, post_data = mocks.mock_out_post_users(id, 'test@email.com')
        user = mommy.make(models.KagisoUser, id=None)
        url = mocks.mock_out_delete_sessions(id)

        did_sign_out = user.record_sign_out()

        assert len(responses.calls) == 2
        assert responses.calls[1].request.url == url

        assert did_sign_out

    @responses.activate
    def test_record_sign_out_invalid_status_code_raises(self):
        id = 1
        _, post_data = mocks.mock_out_post_users(id, 'test@email.com')
        user = mommy.make(models.KagisoUser, id=None)
        mocks.mock_out_delete_sessions(id, status=500)

        with pytest.raises(CASUnexpectedStatusCode):
            did_sign_out = user.record_sign_out()
            assert not did_sign_out

    @responses.activate
    def test_generate_reset_password_token(self):
        _, post_data = mocks.mock_out_post_users(1, 'test@email.com')
        user = mommy.make(models.KagisoUser, id=None)
        url, data = mocks.mock_out_get_reset_password(user.email)

        reset_password_token = user.generate_reset_password_token()

        assert len(responses.calls) == 2
        assert responses.calls[1].request.url == url

        assert reset_password_token == data['reset_password_token']  # noqa

    @responses.activate
    def test_generate_reset_password_token_invalid_status_raises(self):
        _, post_data = mocks.mock_out_post_users(1, 'test@email.com')
        user = mommy.make(models.KagisoUser, id=None)
        url, data = mocks.mock_out_get_reset_password(user.email, status=500)

        with pytest.raises(CASUnexpectedStatusCode):
            reset_password_token = user.generate_reset_password_token()
            assert reset_password_token is None

    @responses.activate
    def test_reset_password(self):
        _, post_data = mocks.mock_out_post_users(1, 'test@email.com')
        user = mommy.make(models.KagisoUser, id=None)
        url = mocks.mock_out_post_reset_password(user.email)

        did_password_reset = user.reset_password('new_password', 'test_token')

        assert len(responses.calls) == 2
        assert responses.calls[1].request.url == url

        assert did_password_reset

    @responses.activate
    def test_reset_password_invalid_status_code_raises(self):
        _, post_data = mocks.mock_out_post_users(1, 'test@email.com')
        user = mommy.make(models.KagisoUser, id=None)
        mocks.mock_out_post_reset_password(user.email, status=500)

        with pytest.raises(CASUnexpectedStatusCode):
            did_password_reset = user.reset_password(
                'new_password',
                'test_token'
            )

            assert not did_password_reset
