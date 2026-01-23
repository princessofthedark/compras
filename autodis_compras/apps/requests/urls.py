"""
URLs para el módulo de solicitudes.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'requests'

router = DefaultRouter()
# TODO: Registrar viewsets aquí

urlpatterns = [
    path('', include(router.urls)),
]
