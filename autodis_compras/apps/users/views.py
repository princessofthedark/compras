"""
ViewSets para el módulo de usuarios.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Area, Location, CostCenter, User
from .serializers import (
    AreaSerializer, LocationSerializer, CostCenterSerializer,
    UserSerializer, UserCreateSerializer, UserProfileSerializer,
)


class IsFinanceOrDirector(permissions.BasePermission):
    """Solo Finanzas o Dirección General pueden gestionar."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.can_manage_budgets()


class IsManagerOrAbove(permissions.BasePermission):
    """Gerentes, Finanzas o Dirección General pueden gestionar usuarios."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.can_manage_users()


class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [permissions.IsAuthenticated, IsFinanceOrDirector]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated, IsFinanceOrDirector]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name']


class CostCenterViewSet(viewsets.ModelViewSet):
    queryset = CostCenter.objects.select_related('area', 'location').all()
    serializer_class = CostCenterSerializer
    permission_classes = [permissions.IsAuthenticated, IsFinanceOrDirector]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['area', 'location', 'is_active']
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name']


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related('area', 'location', 'cost_center').all()
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'area', 'location', 'is_active', 'is_out_of_office']
    search_fields = ['email', 'first_name', 'last_name', 'username']
    ordering_fields = ['email', 'first_name', 'last_name', 'created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action == 'me':
            return UserProfileSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_finance() or user.is_general_director():
            return self.queryset
        if user.is_manager():
            return self.queryset.filter(area=user.area)
        return self.queryset.filter(pk=user.pk)

    @action(detail=False, methods=['get', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Endpoint para ver/editar el perfil propio."""
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
