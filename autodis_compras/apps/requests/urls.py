"""
URLs para el módulo de solicitudes.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PurchaseRequestViewSet, RequestCommentViewSet, RequestAttachmentViewSet

app_name = 'requests'

router = DefaultRouter()
router.register(r'purchase-requests', PurchaseRequestViewSet)
router.register(r'comments', RequestCommentViewSet)
router.register(r'attachments', RequestAttachmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
