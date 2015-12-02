# Kagiso Auth

[ ![Codeship Status for Kagiso-Future-Media/django_auth](https://codeship.com/projects/f5876350-c731-0132-3b15-4a390261e3f5/status?branch=master)](https://codeship.com/projects/74869)
[![codecov.io](https://codecov.io/github/Kagiso-Future-Media/django_auth/coverage.svg?token=LrFwE9TaXk&branch=master)](https://codecov.io/github/Kagiso-Future-Media/django_auth?branch=master)

## Installation
`pip install kagiso_django_auth`

## Usage
Add kagiso_auth to the list of `INSTALLED_APPS` in your settings.py:

```
INSTALLED_APPS = (
    # ...,
    'kagiso_auth',
)
```

Then add the custom backend to the list of 'AUTHENTICATION_BACKENDS`:

```
AUTHENTICATION_BACKENDS = (
    # ...
    'kagiso_auth.backends.KagisoBackend',
)
```

Then specify that Django is to use the `KagisoUser` model as its user model.

```
AUTH_USER_MODEL = 'kagiso_auth.KagisoUser'
```

If you want to use the generic auth UI for sign ups and password resets etc,
add the following to your urls.py:

```
from kagiso_auth import urls as kagiso_auth_urls
url(r'', include(kagiso_auth_urls)),
```

Finally you need to add your Auth API (https://github.com/Kagiso-Future-Media/auth) credentials to settings.py.
In production make sure you read them in from an environment variable.

```
AUTH_API_TOKEN = 'your-token'
AUTH_API_BASE_URL (optional - defaults to https://auth.kagiso.io) = 'xyz'
```

## Testing
This library uses Pytest-Django (https://pytest-django.readthedocs.org/en/latest/).

```
pip install -r requirements.txt
py.test
py.test --ds=kagiso_auth.tests.settings.ci # For Codeship
```

To run the integration tests (excluded by default as they are slow):
```
py.test kagiso_auth/tests/integration/test_integration.py
```
