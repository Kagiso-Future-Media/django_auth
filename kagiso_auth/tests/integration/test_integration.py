from django.conf import settings
from django.test import TestCase
from model_mommy import mommy
import pytest

from . import utils
from ... import models
from ...backends import KagisoBackend
from ...exceptions import EmailNotConfirmedError


class KagisoUserTest(TestCase):

    def test_user(self):
        # ----- Create user -----
        email = utils.random_email()
        profile = {
            'age': 15,
        }
        password = 'my_password'

        user = mommy.prepare(
            models.KagisoUser,
            id=None,
            email=email,
            first_name='George',
            last_name='Smith',
            profile=profile,
            created_via=settings.APP_NAME
        )
        user.set_password(password)
        user.save()

        auth_backend = KagisoBackend()

        result = models.KagisoUser.objects.get(id=user.id)

        assert result.email == user.email
        assert result.first_name == user.first_name
        assert result.last_name == user.last_name
        assert not result.confirmation_token
        assert result.profile == profile
        assert result.created_via == user.created_via

        # ----- Unconfirmed users can't sign in -----
        with pytest.raises(EmailNotConfirmedError):
            auth_backend.authenticate(
                email=user.email,
                password=password
            )

        # ----- Confirm user -----
        assert not user.email_confirmed
        user.confirm_email(user.confirmation_token)
        assert user.email_confirmed

        # ----- Regenerate confirmation token -----
        token = user.regenerate_confirmation_token
        assert token

        # ----- Can the user sign in? -----
        signed_in_user = auth_backend.authenticate(
            email=user.email,
            password=password
        )
        assert signed_in_user == user
        assert signed_in_user.last_sign_in_via == settings.APP_NAME

        # ----- Update user -----
        new_email = utils.random_email()
        new_first_name = 'Fred'
        new_last_name = 'Jones'
        new_profile = {
            'age': 50,
        }

        user.email = new_email
        user.first_name = new_first_name
        user.last_name = new_last_name
        user.is_staff = False
        user.is_superuser = False
        user.profile = new_profile
        user.save()

        updated_result = models.KagisoUser.objects.get(id=user.id)

        assert updated_result.email == new_email
        assert updated_result.first_name == new_first_name
        assert updated_result.last_name == new_last_name
        assert not updated_result.is_staff
        assert not updated_result.is_superuser
        assert updated_result.profile == new_profile

        # ----- Sign out the user -----
        signed_out = user.record_sign_out()
        assert signed_out

        # ----- Delete user -----
        updated_result.delete()

    def test_social_sign_in(self):
        # ----- Create user -----
        email = utils.random_email()

        user = mommy.prepare(
            models.KagisoUser,
            id=None,
            email=email,
        )
        user.set_unusable_password()
        user.save()
        user.confirm_email(user.confirmation_token)

        # ----- Can the user sign in? -----
        auth_backend = KagisoBackend()
        signed_in_user = auth_backend.authenticate(
            email=user.email,
            strategy='facebook'
        )

        assert signed_in_user == user

    def test_reset_password(self):
        # ----- Create the user -----
        email = utils.random_email()

        user = mommy.prepare(
            models.KagisoUser,
            id=None,
            email=email,
        )
        user.set_password('password')
        user.save()
        user.confirm_email(user.confirmation_token)

        # ----- Reset the password -----
        new_password = 'new_password'
        token = user.generate_reset_password_token()
        did_password_reset = user.reset_password(new_password, token)
        assert did_password_reset

        # ----- Can the user still sign in? -----
        auth_backend = KagisoBackend()
        result = auth_backend.authenticate(
            email=user.email,
            password=new_password
        )
        assert result == user
