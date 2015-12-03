from django.contrib.auth.backends import ModelBackend

from . import http
from .auth_api_client import AuthApiClient
from .exceptions import AuthAPIUnexpectedStatusCode, EmailNotConfirmedError
from .models import KagisoUser


class KagisoBackend(ModelBackend):

    # Django calls our backend with username='xyz', password='abc'
    # e.g. credentials = {'username': 'Fred', 'password': 'open'}
    # authenticate(**credentials), even though we set USERNAME_FIELD to
    # 'email' in models.py.
    #
    # Django AllAuth does this:
    #  credentials = {'email': 'test@kagiso.io, 'password': 'open'}
    def authenticate(self, email=None, username=None, password=None, **kwargs):
        email = username if not email else email

        payload = {
            'email': email,
        }

        # Social signins don't have passwords
        if password:
            payload['password'] = password

        # Support social sign_ins
        strategy = kwargs.get('strategy')
        if strategy:
            payload['strategy'] = strategy

        auth_api_client = AuthApiClient()
        status, data = auth_api_client.call('sessions', 'POST', payload)

        if status == http.HTTP_200_OK:
            user = KagisoUser.sync_user_data_locally(data)
        elif status == http.HTTP_404_NOT_FOUND:
            return None
        elif status == http.HTTP_422_UNPROCESSABLE_ENTITY:
            raise EmailNotConfirmedError()
        else:
            raise AuthAPIUnexpectedStatusCode(status, data)

        return user
