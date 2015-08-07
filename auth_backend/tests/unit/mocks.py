import json

import responses


def mock_out_post_users(id, email, **kwargs):
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
        'created': '2015-04-21T08:18:30.368602Z',
        'modified': '2015-04-21T08:18:30.374410Z'
    }

    responses.add(
        responses.POST,
        url,
        body=json.dumps(data),
        status=201,
    )

    return url, data


def mock_out_put_users(id, email, **kwargs):
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
        'modified': '2015-04-21T08:18:30.374410Z'
    }

    responses.add(
        responses.PUT,
        url,
        body=json.dumps(data),
        status=200,
    )

    return url, data


def mock_out_delete_users(id):
    url = 'https://auth.kagiso.io/api/v1/users/{id}/.json'.format(id=id)

    responses.add(
        responses.DELETE,
        url,
        status=204,
    )

    return url


def mock_out_post_confirm_email(id):
    url = 'https://auth.kagiso.io/api/v1/users/{id}/confirm_email/.json'.format(id=id)  # noqa

    responses.add(
        responses.POST,
        url,
        status=200,
    )

    return url


def mock_out_get_reset_password(id):
    url = 'https://auth.kagiso.io/api/v1/users/{id}/reset_password/.json'.format(id=id)  # noqa
    data = {
        'reset_password_token': 'random_token',
    }

    responses.add(
        responses.GET,
        url,
        body=json.dumps(data),
        status=200,
    )

    return url, data


def mock_out_post_reset_password(id):
    url = 'https://auth.kagiso.io/api/v1/users/{id}/reset_password/.json'.format(id=id)  # noqa

    responses.add(
        responses.POST,
        url,
        status=200,
    )

    return url


def mock_out_post_sessions(status):
    url = 'https://auth.kagiso.io/api/v1/sessions/.json'

    responses.add(
        responses.POST,
        url,
        status=status,
    )

    return url


def mock_out_delete_sessions(id):
    url = 'https://auth.kagiso.io/api/v1/sessions/{id}/.json'.format(id=id)

    responses.add(
        responses.DELETE,
        url,
        status=200,
    )

    return url
