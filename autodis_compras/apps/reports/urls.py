"""
URLs para el módulo de reportes.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'reports'

router = DefaultRouter()
# TODO: Registrar viewsets aquí

urlpatterns = [
    path('', include(router.urls)),
]
