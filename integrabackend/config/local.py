import os
import sentry_sdk
from .common import Common
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Local(Common):
    DEBUG = True

    # Testing
    if not DEBUG:
        sentry_sdk.init(
            dsn="https://0f2c75c7488b4afe90ff95e5c426f889@o82137.ingest.sentry.io/1538689",
            integrations=[DjangoIntegration()],

            # If you wish to associate users to errors (assuming you are using
            # django.contrib.auth) you may enable sending PII data.
            send_default_pii=True
        )

    INSTALLED_APPS = Common.INSTALLED_APPS
    INSTALLED_APPS += ('django_nose',)
    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
    NOSE_ARGS = ['-s',]

    # Mail
    # EMAIL_HOST = 'localhost'
    # EMAIL_PORT = 1025
    # EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

    # DATABASES = {
    #     'default': {
    #         'ENGINE': 'django.db.backends.sqlite3',
    #         'NAME': 'mydatabase',
    #     }
    # }
