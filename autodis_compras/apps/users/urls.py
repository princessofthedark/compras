"""
URLs para el módulo de usuarios.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AreaViewSet, LocationViewSet, CostCenterViewSet, UserViewSet

app_name = 'users'

router = DefaultRouter()
router.register(r'areas', AreaViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'cost-centers', CostCenterViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
