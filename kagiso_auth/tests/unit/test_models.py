from dateutil import parser
from django.conf import settings
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from model_mommy import mommy
import pytest
import responses

from . import mocks
from ... import http
from ...exceptions import AuthAPIUnexpectedStatusCode
from ...models import KagisoUser


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

        url, api_data = mocks.post_users(
            1,
            email,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_superuser=is_superuser,
            profile=profile,
        )
        # ------------------------
        # -------Act--------------
        # ------------------------

        user = mommy.make(
            KagisoUser,
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

        result = KagisoUser.objects.get(id=user.id)

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
        assert result.created == parser.parse(api_data['created'])
        assert result.created_via == settings.APP_NAME
        assert result.modified == parser.parse(api_data['modified'])

    @responses.activate
    def test_create_raises_if_user_exists_on_auth_api(self):
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

        url, api_data = mocks.post_users(
            1,
            email,
            status=http.HTTP_409_CONFLICT,
            **data
        )

        with pytest.raises(IntegrityError):
            mommy.make(
                KagisoUser,
                id=None,
                email=email,
            )

    @responses.activate
    def test_create_invalid_status_code_raises(self):
        email = 'test@email.com'
        mocks.post_users(
            1,
            email,
            status=http.HTTP_500_INTERNAL_SERVER_ERROR
        )

        with pytest.raises(AuthAPIUnexpectedStatusCode):
            mommy.make(
                KagisoUser,
                id=None,
                email=email,
            )

    @responses.activate
    def test_update(self):
        # ------------------------
        # -------Arrange----------
        # ------------------------
        mocks.post_users(1, 'test@email.com')

        user = mommy.make(KagisoUser, id=None)

        email = 'test@email.com'
        first_name = 'Fred'
        last_name = 'Smith'
        is_staff = True
        is_superuser = True
        profile = {
            'age': 22
        }

        url, api_data = mocks.put_users(
            1,
            email,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_superuser=is_superuser,
            profile=profile,
            last_sign_in_via=settings.APP_NAME
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
        user.last_sign_in_via = settings.APP_NAME
        user.save()

        # ------------------------
        # -------Assert----------
        # ------------------------
        result = KagisoUser.objects.get(id=user.id)

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
        assert result.last_sign_in_via == api_data['last_sign_in_via']

    @responses.activate
    def test_update_syncs_if_user_doesnt_exist_on_auth_api(self):
        # ------------------------
        # -------Arrange----------
        # ------------------------
        post_url, _ = mocks.post_users(1, 'test@email.com')

        user = mommy.make(KagisoUser, id=None)

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

        put_url, api_data = mocks.put_users(
            1,
            email,
            status=http.HTTP_404_NOT_FOUND,
        )
        post_url, _ = mocks.post_users(2, 'test@email.com', **data)

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
        result = KagisoUser.objects.get(id=user.id)

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
        mocks.post_users(1, 'test@email.com')
        user = mommy.make(KagisoUser, id=None)
        email = 'test@email.com'
        url, api_data = mocks.put_users(
            1, email, status=http.HTTP_500_INTERNAL_SERVER_ERROR)

        user.email = email

        with pytest.raises(AuthAPIUnexpectedStatusCode):
            user.save()

    @responses.activate
    def test_delete(self):
        mocks.post_users(1, 'test@email.com')
        user = mommy.make(KagisoUser, id=None)
        url = mocks.delete_users(user.id)

        user.delete()

        user_deleted = not KagisoUser.objects.filter(
            id=user.id).exists()

        assert len(responses.calls) == 2
        assert responses.calls[1].request.url == url

        assert user_deleted

    @responses.activate
    def test_delete_invalid_status_code_raises(self):
        mocks.post_users(1, 'test@email.com')
        user = mommy.make(KagisoUser, id=None)
        mocks.delete_users(
            user.id, status=http.HTTP_500_INTERNAL_SERVER_ERROR)

        with pytest.raises(AuthAPIUnexpectedStatusCode):
            user.delete()

    def test_get_full_name_returns_email(self):
        email = 'test@email.com'
        user = KagisoUser(email=email)

        assert user.get_full_name() == email

    def test_get_short_name_returns_email(self):
        email = 'test@email.com'
        user = KagisoUser(email=email)

        assert user.get_short_name() == email

    def test_set_password(self):
        user = KagisoUser()
        password = 'my_password'

        user.set_password(password)

        assert user.raw_password == password

    def test_get_username_returns_email(self):
        email = 'test@email.com'
        user = KagisoUser(email=email)

        assert user.username == email

    def test_set_username_sets_username(self):
        username = 'test@username.com'
        user = KagisoUser(username=username)

        assert user.email == username

    @responses.activate
    def test_get_user_from_auth_db_returns_user_if_exists(self):
        email = 'test@email.com'
        url, _ = mocks.get_user_by_email(1, email)

        result = KagisoUser.get_user_from_auth_db(email)

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == url

        assert result.email == email

    @responses.activate
    def test_get_user_from_auth_db_returns_none_if_not_exists(self):
        email = 'test@email.com'
        url, _ = mocks.get_user_by_email(1, email, http.HTTP_404_NOT_FOUND)

        result = KagisoUser.get_user_from_auth_db(email)

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == url

        assert not result

    @responses.activate
    def test_get_user_from_auth_db_invalid_status_code_raises(self):
        email = 'test@email.com'
        url, _ = mocks.get_user_by_email(
            1,
            email,
            http.HTTP_500_INTERNAL_SERVER_ERROR
        )

        with pytest.raises(AuthAPIUnexpectedStatusCode):
            KagisoUser.get_user_from_auth_db(email)

    @responses.activate
    def test_sync_user_data_locally_syncs_if_no_local_user(self):
        email = 'test@email.com'

        data = {
            'id': 55,
            'email': email,
            'first_name': 'Fred',
            'last_name': 'Smith',
            'is_staff': True,
            'is_superuser': True,
            'profile': {'age': 40, },
            'created': str(timezone.now()),
            'modified': str(timezone.now()),
            'created_via': settings.APP_NAME,
            'last_sign_in_via': settings.APP_NAME
        }

        KagisoUser.sync_user_data_locally(data)

        result = KagisoUser.objects.get(email=email)

        assert result.id == data['id']
        assert result.email == data['email']
        assert result.first_name == data['first_name']
        assert result.last_name == data['last_name']
        assert result.is_staff == data['is_staff']
        assert result.is_superuser == data['is_superuser']
        assert result.profile == data['profile']
        assert result.created_via == settings.APP_NAME
        assert result.last_sign_in_via == settings.APP_NAME

    @responses.activate
    def test_confirm_email(self):
        _, post_data = mocks.post_users(1, 'test@email.com')
        user = mommy.make(KagisoUser, id=None)
        mocks.put_users(
            user.id,
            user.email,
            profile=user.profile
        )
        url = mocks.post_confirm_email()

        user.confirm_email(post_data['confirmation_token'])

        assert len(responses.calls) == 3
        # Create user, confirm user, update user...
        assert responses.calls[1].request.url == url

        result = KagisoUser.objects.get(id=user.id)

        assert result.email_confirmed
        assert not result.confirmation_token

    @responses.activate
    def test_confirm_email_invalid_status_code_raises(self):
        _, post_data = mocks.post_users(1, 'test@email.com')
        user = mommy.make(KagisoUser, id=None)
        mocks.put_users(
            user.id,
            user.email,
            profile=user.profile
        )
        mocks.post_confirm_email(
            status=http.HTTP_500_INTERNAL_SERVER_ERROR)

        with pytest.raises(AuthAPIUnexpectedStatusCode):
            user.confirm_email(post_data['confirmation_token'])

        assert not user.email_confirmed

    @responses.activate
    def test_regenerate_confirmation_token(self):
        _, post_data = mocks.post_users(1, 'test@email.com')
        user = mommy.make(KagisoUser, id=None)
        url, data = mocks.get_regenerate_confirmation_token(
            user.email)

        token = user.regenerate_confirmation_token()

        assert len(responses.calls) == 2
        assert responses.calls[1].request.url == url

        assert token == data['confirmation_token']

    @responses.activate
    def test_regenerate_confirmation_token_raises(self):
        _, post_data = mocks.post_users(1, 'test@email.com')
        user = mommy.make(KagisoUser, id=None)
        url, data = mocks.get_regenerate_confirmation_token(
            user.email,
            http.HTTP_500_INTERNAL_SERVER_ERROR)

        with pytest.raises(AuthAPIUnexpectedStatusCode):
            token = user.regenerate_confirmation_token()
            assert token is None

    @responses.activate
    def test_generate_reset_password_token(self):
        _, post_data = mocks.post_users(1, 'test@email.com')
        user = mommy.make(KagisoUser, id=None)
        url, data = mocks.get_reset_password(user.email)

        reset_password_token = user.generate_reset_password_token()

        assert len(responses.calls) == 2
        assert responses.calls[1].request.url == url

        assert reset_password_token == data['reset_password_token']  # noqa

    @responses.activate
    def test_generate_reset_password_token_invalid_status_raises(self):
        _, post_data = mocks.post_users(1, 'test@email.com')
        user = mommy.make(KagisoUser, id=None)
        url, data = mocks.get_reset_password(
            user.email, status=http.HTTP_500_INTERNAL_SERVER_ERROR)

        with pytest.raises(AuthAPIUnexpectedStatusCode):
            reset_password_token = user.generate_reset_password_token()
            assert reset_password_token is None

    @responses.activate
    def test_reset_password(self):
        _, post_data = mocks.post_users(1, 'test@email.com')
        user = mommy.make(KagisoUser, id=None)
        url = mocks.post_reset_password(user.email)

        did_password_reset = user.reset_password('new_password', 'test_token')

        assert len(responses.calls) == 2
        assert responses.calls[1].request.url == url

        assert did_password_reset

    @responses.activate
    def test_reset_password_invalid_status_code_raises(self):
        _, post_data = mocks.post_users(1, 'test@email.com')
        user = mommy.make(KagisoUser, id=None)
        mocks.post_reset_password(
            user.email, status=http.HTTP_500_INTERNAL_SERVER_ERROR)

        with pytest.raises(AuthAPIUnexpectedStatusCode):
            did_password_reset = user.reset_password(
                'new_password',
                'test_token'
            )

            assert not did_password_reset

    @responses.activate
    def test_record_sign_out(self):
        id = 1
        _, post_data = mocks.post_users(id, 'test@email.com')
        user = mommy.make(KagisoUser, id=None)
        url = mocks.delete_sessions(id)

        did_sign_out = user.record_sign_out()

        assert len(responses.calls) == 2
        assert responses.calls[1].request.url == url

        assert did_sign_out

    @responses.activate
    def test_record_sign_out_invalid_status_code_raises(self):
        id = 1
        _, post_data = mocks.post_users(id, 'test@email.com')
        user = mommy.make(KagisoUser, id=None)
        mocks.delete_sessions(
            id, status=http.HTTP_500_INTERNAL_SERVER_ERROR)

        with pytest.raises(AuthAPIUnexpectedStatusCode):
            did_sign_out = user.record_sign_out()
            assert not did_sign_out

    def test_age_returns_none_when_profile_is_none(self):
        user = KagisoUser(
            email='test@email.com',
        )

        assert user.age is None

    def test_age_returns_none_when_birth_date_doesnt_exist(self):
        user = KagisoUser(
            email='test@email.com',
            profile={}
        )

        assert user.age is None

    def test_age_returns_user_age(self):
        user = KagisoUser(
            email='test@email.com',
            profile={
                'birth_date': '2000-01-19'
            }
        )

        with freeze_time('2016-02-01'):
            expected_age = 16
            assert user.age == expected_age
