"""
Serializers para el módulo de usuarios.
"""

from rest_framework import serializers
from .models import Area, Location, CostCenter, User


class AreaSerializer(serializers.ModelSerializer):
    name_display = serializers.CharField(source='get_name_display', read_only=True)

    class Meta:
        model = Area
        fields = ['id', 'name', 'name_display', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class LocationSerializer(serializers.ModelSerializer):
    name_display = serializers.CharField(source='get_name_display', read_only=True)

    class Meta:
        model = Location
        fields = ['id', 'name', 'name_display', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class CostCenterSerializer(serializers.ModelSerializer):
    area_name = serializers.CharField(source='area.get_name_display', read_only=True)
    location_name = serializers.CharField(source='location.get_name_display', read_only=True, default=None)

    class Meta:
        model = CostCenter
        fields = [
            'id', 'code', 'name', 'area', 'area_name',
            'location', 'location_name', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    area_name = serializers.CharField(source='area.get_name_display', read_only=True)
    location_name = serializers.CharField(source='location.get_name_display', read_only=True)
    cost_center_name = serializers.CharField(source='cost_center.__str__', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'role', 'role_display', 'area', 'area_name',
            'location', 'location_name', 'cost_center', 'cost_center_name',
            'phone', 'is_out_of_office', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'password', 'role', 'area', 'location', 'cost_center', 'phone',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para que el usuario vea/edite su propio perfil."""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    area_name = serializers.CharField(source='area.get_name_display', read_only=True)
    location_name = serializers.CharField(source='location.get_name_display', read_only=True)
    cost_center_name = serializers.CharField(source='cost_center.__str__', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'role', 'role_display', 'area', 'area_name',
            'location', 'location_name', 'cost_center', 'cost_center_name',
            'phone', 'is_out_of_office', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'email', 'username', 'role', 'area', 'location', 'cost_center',
            'is_active', 'created_at', 'updated_at',
        ]
