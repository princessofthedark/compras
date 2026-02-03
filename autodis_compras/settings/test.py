"""
Test settings for AUTODIS Compras project.
Uses SQLite for fast test execution without PostgreSQL dependency.
"""

from .base import *

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Faster password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable Celery during tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Console email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
