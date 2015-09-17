from setuptools import find_packages, setup


setup(
    name='kagiso_django_auth',
    version='2.1.1',
    author='Kagiso Media',
    author_email='development@kagiso.io',
    description='Kagiso Django AuthBackend',
    url='https://github.com/Kagiso-Future-Media/django_auth',
    packages=find_packages(),
    install_requires=[
            'jsonfield==1.0.3',
            'requests==2.6.0',
    ],
)
