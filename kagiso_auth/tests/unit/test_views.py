from datetime import date
from unittest.mock import MagicMock, patch

from django.core import mail
from django.db.utils import IntegrityError
from django.test import RequestFactory, TestCase

from ... import views
from ...exceptions import EmailNotConfirmedError
from ...models import KagisoUser


class SignUpTest(TestCase):

    def test_sign_up_get(self):
        response = self.client.get('/sign_up/')

        assert response.status_code == 200
        assert b'<h1>Register for an account</h1>' in response.content

    @patch('kagiso_auth.forms.KagisoUser', autospec=True)
    def test_sign_up_post(self, MockKagisoUser):  # noqa
        mock_user = MockKagisoUser.return_value
        mock_user.id = 1
        mock_user.save.return_value = mock_user

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

        response = self.client.post('/sign_up/', data, follow=True)

        message = list(response.context['messages'])[0].message

        assert response.status_code == 200
        assert mock_user.save.called

        assert mock_user.email == data['email']
        assert mock_user.first_name == data['first_name']
        assert mock_user.last_name == data['last_name']
        assert mock_user.profile['mobile'] == data['mobile']
        assert mock_user.profile['gender'] == data['gender']
        assert mock_user.profile['region'] == data['region']
        assert mock_user.profile['birth_date'] == str(data['birth_date'])
        assert mock_user.profile['alerts'] == data['alerts']

        assert (
            'You will receive an email with confirmation instructions shortly. '  # noqa
            'This link will expire within 24 hours.'
            'You will not be able to sign in until you have confirmed your \n'
            'email address'
        ) == message

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to[0] == mock_user.email
        assert mail.outbox[0].subject == 'Confirm Your Account'

    @patch('kagiso_auth.forms.KagisoUser', autospec=True)
    def test_sign_up_user_already_exists_redirects_to_sign_in(self, MockKagisoUser):  # noqa
        mock_user = MockKagisoUser.return_value
        mock_user.save.side_effect = IntegrityError()

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

        response = self.client.post('/sign_up/', data, follow=True)

        message = list(response.context['messages'])[0].message

        assert message == 'You already have an account.'
        self.assertRedirects(response, '/sign_in/')

    @patch('kagiso_auth.views.get_object_or_404', autospec=True)
    def test_confirm_account(self, mock_get_object_or_404):
        mock_instance = mock_get_object_or_404.return_value

        response = self.client.get(
            '/confirm_account/?user_id=1&token=my_token',
            follow=True
        )

        message = list(response.context['messages'])[0].message

        assert response.status_code == 200
        assert 'We have confirmed your details, please sign in below' == message  # noqa
        mock_instance.confirm_email.assert_called_with('my_token')
        assert b'<h1>Sign In</h1>' in response.content


class SignInTest(TestCase):

    def test_sign_in_get(self):
        response = self.client.get('/sign_in/')

        assert response.status_code == 200
        assert b'<h1>Sign In</h1>' in response.content

    @patch('kagiso_auth.views.authenticate', autospec=True)
    def test_sign_in_invalid_credentials(self, mock_authenticate):
        data = {'email': 'bogus@email.com', 'password': 'bogus'}
        mock_authenticate.return_value = None

        response = self.client.post('/sign_in/', data, follow=True)
        message = list(response.context['messages'])[0].message

        assert mock_authenticate.called
        assert message == 'Incorrect email or password'

    @patch('kagiso_auth.views.authenticate', autospec=True)
    def test_sign_in_unconfirmed_email(self, mock_authenticate):
        data = {'email': 'bogus@email.com', 'password': 'bogus'}
        mock_authenticate.side_effect = EmailNotConfirmedError

        response = self.client.post('/sign_in/', data, follow=True)
        message = list(response.context['messages'])[0].message

        assert mock_authenticate.called
        assert message == 'Please first confirm your email address. ' \
            '<a href="/resend_confirmation?email={email}">' \
            'Resend confirmation email</a>'.format(email=data['email'])

    @patch('kagiso_auth.views.KagisoUser', autospec=True)
    def test_resend_confirmation(self, MockKagisoUser):  # noqa
        # ----- Arrange -----
        email = 'mock@user.com'
        user = KagisoUser(email=email)

        mock_filter = MagicMock()
        mock_filter.first.return_value = user
        MockKagisoUser.objects.filter.return_value = mock_filter

        data = {'email': email}

        # ----- Act -----
        response = self.client.get('/resend_confirmation/', data, follow=True)

        # ----- Assert -----
        message = list(response.context['messages'])[0].message

        assert response.status_code == 200
        assert (
            'You will receive an email with confirmation instructions shortly. '  # noqa
            'This link will expire within 24 hours.'
        ) == message

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to[0] == email
        assert mail.outbox[0].subject == 'Confirm Your Account'

    @patch('kagiso_auth.views.login', autospec=True)
    @patch('kagiso_auth.views.authenticate', autospec=True)
    def test_sign_in_valid_credentials(self, mock_authenticate, mock_login):
        mock_user = MagicMock()
        data = {'email': 'test@email.com', 'password': 'secret'}
        mock_authenticate.return_value = mock_user

        response = self.client.post('/sign_in/', data, follow=True)

        assert response.status_code == 200
        assert mock_authenticate.called
        assert mock_login.called
        assert mock_user.is_authenticated()


class OauthTest(TestCase):

    @patch('kagiso_auth.views.KagisoUser', autospec=True)
    @patch('kagiso_auth.views.Authomatic', autospec=True)
    def test_new_user_redirects_to_sign_up_page(  # noqa
        self,
        MockAuthomatic,
        MockKagisoUser):

        oauth_data = {
            'email': 'test@email.com',
            'first_name': 'Fred',
            'last_name': 'Smith',
            'birth_date': str(date(1980, 1, 31)),
            'gender': 'male',
        }
        mock_result = MagicMock()
        mock_result.provider.name = 'facebook'
        mock_result.error = None
        mock_result.user.data = oauth_data

        mock_result.user.email = oauth_data['email']
        mock_result.user.first_name = oauth_data['first_name']
        mock_result.user.last_name = oauth_data['last_name']
        mock_result.user.birth_date = oauth_data['birth_date']
        mock_result.user.gender = oauth_data['gender']

        mock_authomatic = MagicMock()
        mock_authomatic.login.return_value = mock_result
        MockAuthomatic.return_value = mock_authomatic

        MockKagisoUser.get_user_from_auth_db.return_value = None

        response = self.client.get('/oauth/facebook/', follow=True)

        # Social sign up should prefill sign up form
        assert oauth_data['email'] in str(response.content)
        assert oauth_data['first_name'] in str(response.content)
        assert oauth_data['last_name'] in str(response.content)
        assert oauth_data['gender'] in str(response.content)

        assert mock_authomatic.login.called

    @patch('kagiso_auth.views.authenticate', autospec=True)
    @patch('kagiso_auth.views.login', autospec=True)
    @patch('kagiso_auth.views.KagisoUser', autospec=True)
    @patch('kagiso_auth.views.Authomatic', autospec=True)
    def test_existing_user_gets_signed_in(  # noqa
            self,
            MockAuthomatic,
            MockKagisoUser,
            mock_login,
            mock_authenticate):

        user = KagisoUser(email='test@email.com')
        user.save = MagicMock()

        mock_result = MagicMock()
        mock_result.error = None
        mock_result.provider.name = 'facebook'
        mock_authomatic = MagicMock()
        mock_authomatic.login.return_value = mock_result
        MockAuthomatic.return_value = mock_authomatic
        mock_authenticate.return_value = user

        response = self.client.get('/oauth/facebook/', follow=True)

        self.assertRedirects(response, '/')
        assert mock_authomatic.login.called
        assert mock_login.called
        assert mock_authenticate.called

    @patch('kagiso_auth.views.authenticate', autospec=True)
    @patch('kagiso_auth.views.login', autospec=True)
    @patch('kagiso_auth.views.KagisoUser', autospec=True)
    @patch('kagiso_auth.views.Authomatic', autospec=True)
    def test_oauth_error_redirects_to_sign_in_page(  # noqa
            self,
            MockAuthomatic,
            MockKagisoUser,
            mock_login,
            mock_authenticate):

        user = KagisoUser(email='test@email.com')
        user.save = MagicMock()

        mock_result = MagicMock()
        mock_result.error = True

        response = self.client.get('/oauth/facebook/', follow=True)

        self.assertRedirects(response, '/sign_in/')


class SignOutTest(TestCase):

    @patch('kagiso_auth.views.logout', autospec=True)
    def test_sign_out(self, mock_logout):
        site = MagicMock()
        site.hostname = 'jacarandafm.com'
        user = KagisoUser()
        user.record_sign_out = MagicMock()

        request_factory = RequestFactory()
        request = request_factory.get('/sign_out/')
        request.site = site
        request.user = user

        response = views.sign_out(request)

        assert response.status_code == 302
        assert user.record_sign_out.called
        assert mock_logout.called


class ForgotPasswordTest(TestCase):

    def test_forgot_password_get(self):
        response = self.client.get('/forgot_password/')

        assert response.status_code == 200
        assert b'<h1>Forgot Password</h1>' in response.content

    @patch('kagiso_auth.views.KagisoUser', autospec=True)
    def test_forgot_password_post_user_not_found(self, MockKagisoUser):  # noqa
        MockKagisoUser.get_user_from_auth_db.return_value = None
        data = {'email': 'no@user.com'}

        response = self.client.post('/forgot_password/', data, follow=True)
        message = list(response.context['messages'])[0].message

        assert response.status_code == 200
        assert 'We could not find a user for that email address' == message

    @patch('kagiso_auth.views.KagisoUser', autospec=True)
    def test_forgot_password_sends_reset_email(self, MockKagisoUser):  # noqa
        # ----- Arrange -----
        email = 'mock@user.com'

        user = KagisoUser(email=email)
        user.generate_reset_password_token = MagicMock(return_value='token')
        MockKagisoUser.get_user_from_auth_db.return_value = user

        data = {'email': email}

        # ----- Act -----
        response = self.client.post('/forgot_password/', data, follow=True)

        # ----- Assert -----
        message = list(response.context['messages'])[0].message

        assert response.status_code == 200
        assert 'You will receive an email with reset instructions shortly' == message  # noqa

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to[0] == email
        assert mail.outbox[0].subject == 'Password Reset'


class ResetPasswordTest(TestCase):

    def test_reset_password_get(self):
        response = self.client.get('/reset_password/')

        assert response.status_code == 200
        assert b'<h1>Reset Password</h1>' in response.content

    @patch('kagiso_auth.views.KagisoUser', autospec=True)
    def test_reset_password_post(self, MockKagisoUser):  # noqa
        email = 'mock@user.com'
        user = KagisoUser(email=email)
        user.reset_password = MagicMock()

        mock_filter = MagicMock()
        mock_filter.first.return_value = user
        MockKagisoUser.objects.filter.return_value = mock_filter

        data = {
            'email': email,
            'token': 'my_token',
            'password': 'password',
            'confirm_password': 'password'
        }

        response = self.client.post('/reset_password/', data, follow=True)
        message = list(response.context['messages'])[0].message

        assert response.status_code == 200
        assert 'Your password has been reset' == message
        user.reset_password.assert_called_with(data['password'], data['token'])
