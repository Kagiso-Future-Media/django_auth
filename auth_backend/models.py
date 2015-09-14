from dateutil import parser
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.utils import timezone
from jsonfield import JSONField

from .auth_api_client import AuthApiClient
from .exceptions import CASUnexpectedStatusCode
from .managers import AuthManager


class KagisoUser(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = 'email'

    id = models.IntegerField(primary_key=True)
    email = models.EmailField(max_length=250, unique=True)
    first_name = models.CharField(blank=True, null=True, max_length=100)
    last_name = models.CharField(blank=True, null=True, max_length=100)
    is_staff = models.BooleanField(default=False)
    email_confirmed = models.DateTimeField(null=True)
    profile = JSONField(null=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField()
    modified = models.DateTimeField()

    confirmation_token = None
    raw_password = None

    objects = AuthManager()

    def __init__(self, *args, **kwargs):
        self._auth_api_client = AuthApiClient()
        super().__init__(*args, **kwargs)

    def override_cas_credentials(self, cas_credentials):
        self.cas_credentials = cas_credentials
        self._auth_api_client = AuthApiClient(self.cas_credentials)

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    @property
    def username(self):
        return self.email

    @username.setter
    def username(self, value):
        self.email = value

    def set_password(self, raw_password):
        # We don't want to save passwords locally
        self.set_unusable_password()
        # Save them in memory only
        self.raw_password = raw_password

    def confirm_email(self, confirmation_token):
        payload = {'confirmation_token': confirmation_token}
        endpoint = 'confirm_email'
        status, data = self._auth_api_client.call(endpoint, 'POST', payload)

        if not status == 200:
            raise CASUnexpectedStatusCode(status, data)

        self.confirmation_token = None
        self.email_confirmed = timezone.now()
        self.save()

    def generate_reset_password_token(self):
        endpoint = 'reset_password/{email}'.format(email=self.email)
        status, data = self._auth_api_client.call(endpoint, 'GET')

        if not status == 200:
            raise CASUnexpectedStatusCode(status, data)

        return data['reset_password_token']

    def reset_password(self, password, reset_password_token):
        payload = {
            'reset_password_token': reset_password_token,
            'password': password,
        }
        endpoint = 'reset_password/{email}'.format(email=self.email)
        status, data = self._auth_api_client.call(endpoint, 'POST', payload)

        if not status == 200:
            raise CASUnexpectedStatusCode(status, data)

        return True

    def record_sign_out(self):
        endpoint = 'sessions/{id}'.format(id=self.id)
        status, data = self._auth_api_client.call(endpoint, 'DELETE')

        if not status == 200:
            raise CASUnexpectedStatusCode(status, data)

        return True

    def build_from_cas_data(self, data):
        self.id = data['id']
        self.email = data['email']
        self.first_name = data.get('first_name', self.first_name)
        self.last_name = data.get('last_name', self.last_name)
        self.is_staff = data.get('is_staff', self.is_staff)
        self.is_superuser = data.get('is_superuser', self.is_superuser)
        self.profile = data.get('profile', self.profile)
        self.confirmation_token = data.get('confirmation_token')
        self.date_joined = parser.parse(data['created'])
        self.modified = parser.parse(data['modified'])

    def _create_user_in_db_and_cas(self):
        payload = {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_staff': self.is_staff,
            'is_superuser': self.is_superuser,
            'profile': self.profile,
            'password': self.raw_password,
        }

        status, data = self._auth_api_client.call('users', 'POST', payload)

        if status not in (201, 409):
            raise CASUnexpectedStatusCode(status, data)

        # 409-Conflict means that the user already exists in CAS
        if status == 409:
            raise IntegrityError('User already exists')

        self.build_from_cas_data(data)

    def _update_user_in_cas(self):
        payload = {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_staff': self.is_staff,
            'is_superuser': self.is_superuser,
            'profile': self.profile,
        }

        status, data = self._auth_api_client.call(
            'users/{id}'.format(id=self.id), 'PUT', payload)

        if status == 200:
            self.email = data['email']
            self.first_name = data.get('first_name')
            self.last_name = data.get('last_name')
            self.is_staff = data.get('is_staff')
            self.is_superuser = data.get('is_superuser')
            self.profile = data.get('profile')
            self.modified = parser.parse(data['modified'])
        elif status == 404:
            # It is possible that a user exists locally but not on CAS
            # eg. when converting an existing app to use CAS
            # so on update if the user is not found, then create a CAS user
            self._create_user_in_db_and_cas()
        else:
            raise CASUnexpectedStatusCode(status, data)

    def __str__(self):
        return self.email  # pragma: no cover


@receiver(pre_delete, sender=KagisoUser)
def delete_user_from_cas(sender, instance, *args, **kwargs):
    status, data = instance._auth_api_client.call(
        'users/{id}'.format(id=instance.id), 'DELETE')

    # It is possible but unlikely that a user exists locally but not on CAS
    # eg. when converting an existing app to use CAS
    # So if not found on CAS just proceed to delete locally
    if status not in (204, 404):
        raise CASUnexpectedStatusCode(status, data)


@receiver(pre_save, sender=KagisoUser)
def save_user_to_cas(sender, instance, *args, **kwargs):
    if not instance.id:
        instance._create_user_in_db_and_cas()
    else:
        instance._update_user_in_cas()
