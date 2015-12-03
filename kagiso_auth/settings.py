import os

from django.conf import settings

AUTH_API_TOKEN = os.getenv('AUTH_API_TOKEN') or getattr(
    settings,
    'AUTH_API_TOKEN',
    'CHANGEME'
)

AUTH_API_BASE_URL = os.getenv('AUTH_API_BASE_URL') or getattr(
    settings,
    'AUTH_API_BASE_URL',
    'https://auth.kagiso.io/api/v1'
)
