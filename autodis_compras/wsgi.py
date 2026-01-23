"""
WSGI config for autodis_compras project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autodis_compras.settings.production')

application = get_wsgi_application()
