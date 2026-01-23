"""
ASGI config for autodis_compras project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autodis_compras.settings.production')

application = get_asgi_application()
