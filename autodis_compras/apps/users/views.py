"""
ViewSets para el módulo de usuarios.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view

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


@extend_schema_view(list=extend_schema(tags=['Áreas']), retrieve=extend_schema(tags=['Áreas']),
                     create=extend_schema(tags=['Áreas']), update=extend_schema(tags=['Áreas']),
                     partial_update=extend_schema(tags=['Áreas']), destroy=extend_schema(tags=['Áreas']))
class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [permissions.IsAuthenticated, IsFinanceOrDirector]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']


@extend_schema_view(list=extend_schema(tags=['Ubicaciones']), retrieve=extend_schema(tags=['Ubicaciones']),
                     create=extend_schema(tags=['Ubicaciones']), update=extend_schema(tags=['Ubicaciones']),
                     partial_update=extend_schema(tags=['Ubicaciones']), destroy=extend_schema(tags=['Ubicaciones']))
class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated, IsFinanceOrDirector]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name']


@extend_schema_view(list=extend_schema(tags=['Centros de Costos']), retrieve=extend_schema(tags=['Centros de Costos']),
                     create=extend_schema(tags=['Centros de Costos']), update=extend_schema(tags=['Centros de Costos']),
                     partial_update=extend_schema(tags=['Centros de Costos']), destroy=extend_schema(tags=['Centros de Costos']))
class CostCenterViewSet(viewsets.ModelViewSet):
    queryset = CostCenter.objects.select_related('area', 'location').all()
    serializer_class = CostCenterSerializer
    permission_classes = [permissions.IsAuthenticated, IsFinanceOrDirector]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['area', 'location', 'is_active']
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name']


@extend_schema_view(list=extend_schema(tags=['Usuarios']), retrieve=extend_schema(tags=['Usuarios']),
                     create=extend_schema(tags=['Usuarios']), update=extend_schema(tags=['Usuarios']),
                     partial_update=extend_schema(tags=['Usuarios']), destroy=extend_schema(tags=['Usuarios']),
                     me=extend_schema(tags=['Usuarios']), change_password=extend_schema(tags=['Usuarios']),
                     toggle_out_of_office=extend_schema(tags=['Usuarios']))
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

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        """Cambiar contraseña del usuario autenticado."""
        current_password = request.data.get('current_password', '')
        new_password = request.data.get('new_password', '')
        confirm_password = request.data.get('confirm_password', '')

        if not current_password or not new_password:
            return Response(
                {'error': 'Debe proporcionar la contraseña actual y la nueva.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not request.user.check_password(current_password):
            return Response(
                {'error': 'La contraseña actual es incorrecta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if new_password != confirm_password:
            return Response(
                {'error': 'Las contraseñas nuevas no coinciden.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(new_password) < 8:
            return Response(
                {'error': 'La contraseña debe tener al menos 8 caracteres.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        try:
            validate_password(new_password, request.user)
        except ValidationError as e:
            return Response(
                {'error': e.messages[0]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.save()
        return Response({'message': 'Contraseña actualizada correctamente.'})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def toggle_out_of_office(self, request):
        """Activar/desactivar estado Fuera de Oficina."""
        user = request.user
        user.is_out_of_office = not user.is_out_of_office
        user.save(update_fields=['is_out_of_office'])
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)
