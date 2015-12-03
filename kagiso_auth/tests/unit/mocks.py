import json

from django.conf import settings
import responses

from ... import http


def get_user_by_email(id, email, status=http.HTTP_200_OK, **kwargs):
    url = 'https://auth.kagiso.io/api/v1/users/{email}/.json'.format(email=email)  # noqa
    data = {
        'id': id,
        'email': email,
        'first_name': kwargs.get('first_name', ''),
        'last_name': kwargs.get('last_name', ''),
        'is_staff': kwargs.get('is_staff', False),
        'is_superuser': kwargs.get('is_superuser', False),
        'confirmation_token': '49:1YkTO2:1VuxvGJre66xqQj6rkEXewmVs08',
        'email_confirmed': None,
        'profile': kwargs.get('profile'),
        'created_via': settings.APP_NAME,
        'created': '2015-04-21T08:18:30.368602Z',
        'modified': '2015-04-21T08:18:30.374410Z'
    }

    responses.add(
        responses.GET,
        url,
        body=json.dumps(data),
        status=status
    )

    return url, data


def post_users(id, email, status=http.HTTP_201_CREATED, **kwargs):
    url = 'https://auth.kagiso.io/api/v1/users/.json'
    data = {
        'id': id,
        'email': email,
        'first_name': kwargs.get('first_name', ''),
        'last_name': kwargs.get('last_name', ''),
        'is_staff': kwargs.get('is_staff', False),
        'is_superuser': kwargs.get('is_superuser', False),
        'confirmation_token': '49:1YkTO2:1VuxvGJre66xqQj6rkEXewmVs08',
        'email_confirmed': None,
        'profile': kwargs.get('profile'),
        'created_via': settings.APP_NAME,
        'created': '2015-04-21T08:18:30.368602Z',
        'modified': '2015-04-21T08:18:30.374410Z'
    }

    responses.add(
        responses.POST,
        url,
        body=json.dumps(data),
        status=status
    )

    return url, data


def put_users(id, email, status=http.HTTP_200_OK, **kwargs):
    url = 'https://auth.kagiso.io/api/v1/users/{id}/.json'.format(id=id)
    data = {
        'id': 1,
        'email': email,
        'first_name': kwargs.get('first_name', ''),
        'last_name': kwargs.get('last_name', ''),
        'is_staff': kwargs.get('is_staff', False),
        'is_superuser': kwargs.get('is_superuser', False),
        'profile': kwargs.get('profile'),
        'created': '2015-04-21T08:18:30.368602Z',
        'created_via': kwargs.get('created_via'),
        'modified': '2015-04-21T08:18:30.374410Z',
        'last_sign_in_via': kwargs.get('last_sign_in_via'),
    }

    responses.add(
        responses.PUT,
        url,
        body=json.dumps(data),
        status=status
    )

    return url, data


def delete_users(id, status=http.HTTP_204_NO_CONTENT):
    url = 'https://auth.kagiso.io/api/v1/users/{id}/.json'.format(id=id)

    responses.add(
        responses.DELETE,
        url,
        status=status
    )

    return url


def post_confirm_email(status=http.HTTP_200_OK):
    url = 'https://auth.kagiso.io/api/v1/confirm_email/.json'  # noqa

    responses.add(
        responses.POST,
        url,
        status=status
    )

    return url


def get_regenerate_confirmation_token(email, status=http.HTTP_200_OK):
    url = 'https://auth.kagiso.io/api/v1/users/{email}/confirmation_token/.json'.format(email=email)  # noqa
    data = {
        'confirmation_token': 'random_token',
    }

    responses.add(
        responses.GET,
        url,
        body=json.dumps(data),
        status=status,
    )

    return url, data


def get_reset_password(email, status=http.HTTP_200_OK):
    url = 'https://auth.kagiso.io/api/v1/reset_password/{email}/.json'.format(email=email)  # noqa
    data = {
        'reset_password_token': 'random_token',
    }

    responses.add(
        responses.GET,
        url,
        body=json.dumps(data),
        status=status,
    )

    return url, data


def post_reset_password(email, status=http.HTTP_200_OK):
    url = 'https://auth.kagiso.io/api/v1/reset_password/{email}/.json'.format(email=email)  # noqa

    responses.add(
        responses.POST,
        url,
        status=status
    )

    return url


def post_sessions(status=http.HTTP_200_OK, **kwargs):
    url = 'https://auth.kagiso.io/api/v1/sessions/.json'
    data = {
        'id': kwargs.get('id', 1),
        'email': kwargs.get('email'),
        'first_name': kwargs.get('first_name', ''),
        'last_name': kwargs.get('last_name', ''),
        'is_staff': kwargs.get('is_staff', False),
        'is_superuser': kwargs.get('is_superuser', False),
        'email_confirmed': None,
        'profile': kwargs.get('profile'),
        'created': '2015-04-21T08:18:30.368602Z',
        'created_via': kwargs.get('created_via'),
        'modified': '2015-04-21T08:18:30.374410Z',
        'last_sign_in_via': kwargs.get('last_sign_in_via'),
    }

    responses.add(
        responses.POST,
        url,
        body=json.dumps(data),
        status=status
    )

    return url, data


def delete_sessions(id, status=http.HTTP_200_OK):
    url = 'https://auth.kagiso.io/api/v1/sessions/{id}/.json'.format(id=id)

    responses.add(
        responses.DELETE,
        url,
        status=status
    )

    return url
