from datetime import datetime

from dateutil import parser
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.utils import timezone
from jsonfield import JSONField

from . import http
from .auth_api_client import AuthApiClient
from .exceptions import AuthAPIUnexpectedStatusCode
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
    created = models.DateTimeField()
    created_via = models.CharField(blank=True, null=True, max_length=100)
    modified = models.DateTimeField()
    last_sign_in_via = models.CharField(blank=True, null=True, max_length=100)

    confirmation_token = None
    raw_password = None

    objects = AuthManager()

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

    @property
    def age(self):
        if self.profile and 'birth_date' in self.profile:
            birth_date = parser.parse(self.profile['birth_date'])
            today = datetime.now()

            passed_delta = relativedelta(today, birth_date)
            return passed_delta.years

    def set_password(self, raw_password):
        # We don't want to save passwords locally
        self.set_unusable_password()
        # Save them in memory only
        self.raw_password = raw_password

    @staticmethod
    def get_user_from_auth_db(email):
        endpoint = 'users/{email}'.format(email=email)
        status, data = AuthApiClient.call(endpoint, 'GET')

        if status == http.HTTP_200_OK:
            user = KagisoUser.objects.filter(email=email).first()
            if not user:
                user = KagisoUser.sync_user_data_locally(data)
            return user
        elif status == http.HTTP_404_NOT_FOUND:
            return None
        else:
            raise AuthAPIUnexpectedStatusCode(status, data)

    @staticmethod
    def sync_user_data_locally(data):
        try:
            pre_save.disconnect(
                save_user_to_auth_api,
                sender=KagisoUser
            )
            user = KagisoUser.objects.filter(
                id=data['id']
            ).first() or KagisoUser()
            user.build_from_auth_api_data(data)
            user.save()
            return user
        finally:
            pre_save.connect(save_user_to_auth_api, sender=KagisoUser)

    def confirm_email(self, confirmation_token):
        payload = {'confirmation_token': confirmation_token}
        endpoint = 'confirm_email'
        status, data = AuthApiClient.call(endpoint, 'POST', payload)

        if not status == http.HTTP_200_OK:
            raise AuthAPIUnexpectedStatusCode(status, data)

        self.confirmation_token = None
        self.email_confirmed = timezone.now()
        self.save()

    def regenerate_confirmation_token(self):
        endpoint = 'users/{email}/confirmation_token'.format(email=self.email)
        status, data = AuthApiClient.call(endpoint, 'GET')

        if not status == http.HTTP_200_OK:
            raise AuthAPIUnexpectedStatusCode(status, data)

        self.confirmation_token = data['confirmation_token']
        return self.confirmation_token

    def generate_reset_password_token(self):
        endpoint = 'reset_password/{email}'.format(email=self.email)
        status, data = AuthApiClient.call(endpoint, 'GET')

        if not status == http.HTTP_200_OK:
            raise AuthAPIUnexpectedStatusCode(status, data)

        return data['reset_password_token']

    def reset_password(self, password, reset_password_token):
        payload = {
            'reset_password_token': reset_password_token,
            'password': password,
        }
        endpoint = 'reset_password/{email}'.format(email=self.email)
        status, data = AuthApiClient.call(endpoint, 'POST', payload)

        if not status == http.HTTP_200_OK:
            raise AuthAPIUnexpectedStatusCode(status, data)

        return True

    def record_sign_out(self):
        endpoint = 'sessions/{id}'.format(id=self.id)
        status, data = AuthApiClient.call(endpoint, 'DELETE')

        if not status == http.HTTP_200_OK:
            raise AuthAPIUnexpectedStatusCode(status, data)

        return True

    def build_from_auth_api_data(self, data):
        self.id = data['id']
        self.email = data['email']
        self.first_name = data.get('first_name', self.first_name)
        self.last_name = data.get('last_name', self.last_name)
        self.is_staff = data.get('is_staff', self.is_staff)
        self.is_superuser = data.get('is_superuser', self.is_superuser)
        self.profile = data.get('profile', self.profile)
        self.confirmation_token = data.get('confirmation_token')
        self.created = parser.parse(data['created'])
        self.created_via = data.get('created_via')
        self.modified = parser.parse(data['modified'])
        self.last_sign_in_via = data.get('last_sign_in_via')

    def _create_user_in_db_and_auth_api(self):
        payload = {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_staff': self.is_staff,
            'is_superuser': self.is_superuser,
            'profile': self.profile,
            'password': self.raw_password,
            'created_via': self.created_via
        }

        status, data = AuthApiClient.call('users', 'POST', payload)

        if status not in (http.HTTP_201_CREATED, http.HTTP_409_CONFLICT):
            raise AuthAPIUnexpectedStatusCode(status, data)

        # 409-Conflict means that the user already exists in AuthAPI
        if status == http.HTTP_409_CONFLICT:
            raise IntegrityError('User already exists')

        self.build_from_auth_api_data(data)

    def _update_user_in_auth_api(self):
        payload = {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_staff': self.is_staff,
            'is_superuser': self.is_superuser,
            'profile': self.profile,
            'last_sign_in_via': self.last_sign_in_via
        }

        status, data = AuthApiClient.call(
            'users/{id}'.format(id=self.id), 'PUT', payload)

        if status == http.HTTP_200_OK:
            self.email = data['email']
            self.first_name = data.get('first_name')
            self.last_name = data.get('last_name')
            self.is_staff = data.get('is_staff')
            self.is_superuser = data.get('is_superuser')
            self.profile = data.get('profile')
            self.modified = parser.parse(data['modified'])
            self.last_sign_in_via = data.get('last_sign_in_via')
        elif status == http.HTTP_404_NOT_FOUND:
            # It is possible that a user exists locally but not on AuthAPI
            # eg. when converting an existing app to use AuthAPI
            # so on update if the user is not found, then create a AuthAPI user
            self._create_user_in_db_and_auth_api()
        else:
            raise AuthAPIUnexpectedStatusCode(status, data)

    def __str__(self):
        return self.email  # pragma: no cover


@receiver(pre_delete, sender=KagisoUser)
def delete_user_from_auth_api(sender, instance, *args, **kwargs):
    status, data = AuthApiClient.call(
        'users/{id}'.format(id=instance.id), 'DELETE')

    # It is possible but unlikely that a user exists locally but not on AuthAPI
    # eg. when converting an existing app to use AuthAPI
    # So if not found on AuthAPI just proceed to delete locally
    if status not in (http.HTTP_204_NO_CONTENT, http.HTTP_404_NOT_FOUND):
        raise AuthAPIUnexpectedStatusCode(status, data)


@receiver(pre_save, sender=KagisoUser)
def save_user_to_auth_api(sender, instance, *args, **kwargs):
    if not instance.id:
        instance._create_user_in_db_and_auth_api()
    else:
        instance._update_user_in_auth_api()
