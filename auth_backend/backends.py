from django.contrib.auth.backends import ModelBackend
from django.db.models.signals import pre_save

from .auth_api_client import AuthApiClient

from .exceptions import CASUnexpectedStatusCode, EmailNotConfirmedError
from .models import KagisoUser, save_user_to_cas


class KagisoBackend(ModelBackend):

    # Django calls our backend with username='xyz', password='abc'
    # e.g. credentials = {'username': 'Fred', 'password': 'open'}
    # authenticate(**credentials), even though we set USERNAME_FIELD to
    # 'email' in models.py.
    #
    # Django AllAuth does this:
    #  credentials = {'email': 'test@kagiso.io, 'password': 'open'}
    def authenticate(self, email=None, username=None, password=None, **kwargs):
        cas_credentials = kwargs.get('cas_credentials')

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

        auth_api_client = AuthApiClient(cas_credentials)
        status, data = auth_api_client.call('sessions', 'POST', payload)

        if status == 200:
            local_user = KagisoUser.objects.filter(id=data['id']).first()
            if local_user:
                local_user.override_cas_credentials(cas_credentials)
            else:
                try:
                    # Do not on save sync to CAS, as we just got the user's
                    # data from CAS, and nothing has changed in the interim
                    pre_save.disconnect(save_user_to_cas, sender=KagisoUser)
                    local_user = KagisoUser()
                    local_user.set_password(password)
                    local_user.build_from_cas_data(data)
                    local_user.save()
                finally:
                    pre_save.connect(save_user_to_cas, sender=KagisoUser)
        elif status == 404:
            return None
        elif status == 422:
            raise EmailNotConfirmedError()
        else:
            raise CASUnexpectedStatusCode(status, data)

        return local_user
