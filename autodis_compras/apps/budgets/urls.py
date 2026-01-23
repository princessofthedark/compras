"""
URLs para el módulo de presupuestos.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'budgets'

router = DefaultRouter()
# TODO: Registrar viewsets aquí

urlpatterns = [
    path('', include(router.urls)),
]
