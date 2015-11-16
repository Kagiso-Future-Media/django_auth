from datetime import date
from unittest.mock import patch

from django import forms as django_forms

from ... import forms


def test_validate_passwords_match_adds_error_to_form():
    class TestForm(django_forms.Form):
        password = django_forms.CharField(
            widget=django_forms.PasswordInput(),
            min_length=8
        )
        confirm_password = django_forms.CharField(
            widget=django_forms.PasswordInput()
        )

    form = TestForm()
    form.cleaned_data = {}
    form.cleaned_data['password'] = 'password'
    form.cleaned_data['confirm_password'] = 'password'

    forms.validate_passwords_match(form)
    assert not form.errors

    form.cleaned_data['confirm_password'] = 'something else'

    forms.validate_passwords_match(form)
    assert form.errors['confirm_password'][0] == 'Passwords do not match'


class TestSignUpForm:

    def test_create_returns_form(self):
        form = forms.SignUpForm.create()

        assert isinstance(form, forms.SignUpForm)
        assert not form.social_sign_in
        assert 'password' in form.fields
        assert 'confirm_password' in form.fields

    def test_create_socially_returns_form_without_password_fields(self):
        form = forms.SignUpForm.create(oauth_data={'x': 'y'})

        assert isinstance(form, forms.SignUpForm)
        assert form.social_sign_in
        assert 'password' not in form.fields
        assert 'confirm_password' not in form.fields

    @patch('auth_backend.forms.KagisoUser', autospec=True)
    def test_save_regular_sign_up_from_regular_django_site(self, MockKagisoUser):  # noqa
        data = {
            'email': 'bogus@email.com',
            'first_name': 'Fred',
            'last_name': 'Smith',
            'password': 'mypassword',
            'confirm_password': 'mypassword',
            'mobile': '123456789',
            'gender': 'MALE',
            'region': 'EASTERN_CAPE',
            'birth_date': date(1980, 1, 31),
            'alerts': ['EMAIL', 'SMS'],
        }
        form = forms.SignUpForm.create(post_data=data)

        assert form.is_valid()

        user = form.save()

        assert user.email == data['email']
        assert user.first_name == data['first_name']
        assert user.last_name == data['last_name']
        assert user.profile['mobile'] == data['mobile']
        assert user.profile['gender'] == data['gender']
        assert user.profile['region'] == data['region']
        assert user.profile['birth_date'] == str(data['birth_date'])
        assert user.profile['alerts'] == data['alerts']

        user.set_password.assert_called_with(data['password'])

    @patch('auth_backend.forms.KagisoUser', autospec=True)
    def test_save_regular_sign_up_from_wagtail_site(self, MockKagisoUser):  # noqa
        site_id = 55
        data = {
            'email': 'bogus@email.com',
            'first_name': 'Fred',
            'last_name': 'Smith',
            'password': 'mypassword',
            'confirm_password': 'mypassword',
            'mobile': '123456789',
            'gender': 'MALE',
            'region': 'EASTERN_CAPE',
            'birth_date': date(1980, 1, 31),
            'alerts': ['EMAIL', 'SMS'],
        }
        form = forms.SignUpForm.create(post_data=data)
        form.site_id = site_id
        assert form.is_valid()

        user = form.save()

        assert user.profile['site_id'] == site_id

    @patch('auth_backend.forms.KagisoUser', autospec=True)
    def test_save_social_sign_up(self, MockKagisoUser):  # noqa
        data = {
            'provider': 'facebook',
            'email': 'bogus@email.com',
            'first_name': 'Fred',
            'last_name': 'Smith',
            'mobile': '123456789',
            'gender': 'MALE',
            'region': 'EASTERN_CAPE',
            'birth_date': date(1980, 1, 31),
            'alerts': ['EMAIL', 'SMS'],
        }
        form = forms.SignUpForm.create(post_data=data, oauth_data=data)
        assert form.is_valid()

        user = form.save()

        assert user.email == data['email']
        assert user.email_confirmed
        assert user.first_name == data['first_name']
        assert user.last_name == data['last_name']
        assert user.profile['mobile'] == data['mobile']
        assert user.profile['gender'] == data['gender']
        assert user.profile['region'] == data['region']
        assert user.profile['birth_date'] == str(data['birth_date'])
        assert user.profile['alerts'] == data['alerts']

        assert not user.set_password.called
