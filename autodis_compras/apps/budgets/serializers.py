"""
Serializers para el módulo de presupuestos.
"""

from rest_framework import serializers
from .models import Category, Item, Budget, BudgetHistory


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'code', 'name', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class ItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Item
        fields = [
            'id', 'category', 'category_name', 'code', 'name',
            'description', 'unit', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class BudgetSerializer(serializers.ModelSerializer):
    cost_center_name = serializers.CharField(source='cost_center.__str__', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    spent_amount = serializers.DecimalField(
        source='get_spent_amount', max_digits=12, decimal_places=2, read_only=True
    )
    available_amount = serializers.DecimalField(
        source='get_available_amount', max_digits=12, decimal_places=2, read_only=True
    )
    utilization_percentage = serializers.FloatField(
        source='get_utilization_percentage', read_only=True
    )
    is_exceeded = serializers.BooleanField(read_only=True)

    class Meta:
        model = Budget
        fields = [
            'id', 'cost_center', 'cost_center_name', 'category', 'category_name',
            'year', 'month', 'amount', 'is_closed',
            'spent_amount', 'available_amount', 'utilization_percentage', 'is_exceeded',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class BudgetHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)

    class Meta:
        model = BudgetHistory
        fields = [
            'id', 'budget', 'previous_amount', 'new_amount',
            'changed_by', 'changed_by_name', 'reason', 'created_at',
        ]
        read_only_fields = ['created_at']
