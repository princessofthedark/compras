"""
URL configuration for autodis_compras project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication (JWT)
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API endpoints
    path('api/users/', include('autodis_compras.apps.users.urls')),
    path('api/requests/', include('autodis_compras.apps.requests.urls')),
    path('api/budgets/', include('autodis_compras.apps.budgets.urls')),
    path('api/reports/', include('autodis_compras.apps.reports.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "AUTODIS - Sistema de Compras"
admin.site.site_title = "AUTODIS Compras"
admin.site.index_title = "Administración del Sistema"
