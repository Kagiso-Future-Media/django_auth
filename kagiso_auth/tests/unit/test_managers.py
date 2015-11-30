from dateutil import parser
from django.test import TestCase
import responses

from . import mocks
from ...models import KagisoUser


class KagisoUserTest(TestCase):

    @responses.activate
    def test_create_user(self):
        email = 'test@email.com'
        first_name = 'Fred'
        last_name = 'Smith'
        is_staff = True
        is_superuser = True
        password = 'random'
        profile = {
            'age': 18,
        }
        url, api_data = mocks.post_users(
            1,
            email,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_superuser=is_superuser,
            profile=profile
        )

        result = KagisoUser.objects.create_user(
            email, password, profile=profile)

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == url

        assert result.id == api_data['id']
        assert result.email == email
        assert result.first_name == first_name
        assert result.last_name == last_name
        assert result.is_staff == is_staff
        assert result.is_superuser == is_superuser
        assert result.confirmation_token == api_data['confirmation_token']
        assert not result.email_confirmed
        assert result.profile == profile
        assert result.created == parser.parse(api_data['created'])
        assert result.modified == parser.parse(api_data['modified'])

    @responses.activate
    def test_create_super_user(self):
        email = 'test@email.com'
        password = 'random'
        url, api_data = mocks.post_users(1, email, is_superuser=True)

        result = KagisoUser.objects.create_superuser(email, password)

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == url

        assert result.email == email
        assert result.is_superuser
