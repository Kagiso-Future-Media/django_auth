from django.contrib.auth.backends import ModelBackend
from django.db.models.signals import pre_save

from . import http
from .auth_api_client import AuthApiClient
from .exceptions import AuthAPIUnexpectedStatusCode, EmailNotConfirmedError
from .models import KagisoUser, save_user_to_auth_api


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
            local_user = KagisoUser.objects.filter(id=data['id']).first()
            if not local_user:
                try:
                    # Do not on save sync to Auth API, as we just got the
                    # data from the API, and nothing has changed in the interim
                    pre_save.disconnect(
                        save_user_to_auth_api,
                        sender=KagisoUser
                    )
                    local_user = KagisoUser()
                    local_user.set_password(password)
                    local_user.build_from_auth_api_data(data)
                    local_user.save()
                finally:
                    pre_save.connect(save_user_to_auth_api, sender=KagisoUser)
        elif status == http.HTTP_404_NOT_FOUND:
            return None
        elif status == http.HTTP_422_UNPROCESSABLE_ENTITY:
            raise EmailNotConfirmedError()
        else:
            raise AuthAPIUnexpectedStatusCode(status, data)

        return local_user
