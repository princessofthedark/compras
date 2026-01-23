"""
URLs para el módulo de usuarios.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'users'

router = DefaultRouter()
# TODO: Registrar viewsets aquí

urlpatterns = [
    path('', include(router.urls)),
]
