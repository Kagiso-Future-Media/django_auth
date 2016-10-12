from setuptools import find_packages, setup


setup(
    name='kagiso_django_auth',
    version='8.1.0',
    author='Kagiso Media',
    author_email='development@kagiso.io',
    description='Kagiso Django AuthBackend',
    url='https://github.com/Kagiso-Future-Media/django_auth',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
            'jsonfield==1.0.3',
            'requests==2.10.0',
            'authomatic==0.1.0.post1'
    ],
)
