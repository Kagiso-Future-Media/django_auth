import os

from django.conf import settings

CAS_TOKEN = os.getenv('CAS_TOKEN') or getattr(
    settings,
    'CAS_TOKEN',
    'CHANGEME'
)
CAS_SOURCE_ID = os.getenv('CAS_SOURCE_ID') or getattr(
    settings,
    'CAS_SOURCE_ID',
    'CHANGEME'
)
CAS_BASE_URL = os.getenv('CAS_BASE_URL') or getattr(
    settings,
    'CAS_BASE_URL',
    'https://auth.kagiso.io/api/v1'
)
