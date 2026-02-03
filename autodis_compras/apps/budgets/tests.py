"""
Tests para el módulo de presupuestos.
"""

from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from autodis_compras.apps.users.models import Area, Location, CostCenter, User
from .models import Category, Item, Budget, BudgetHistory


class BudgetBaseTestCase(TestCase):
    """Caso base con datos compartidos."""

    @classmethod
    def setUpTestData(cls):
        cls.area = Area.objects.create(name=Area.OPERACIONES)
        cls.area_fin = Area.objects.create(name=Area.FINANZAS)
        cls.location = Location.objects.create(name=Location.GUADALAJARA)
        cls.cost_center = CostCenter.objects.create(
            code='CC-OPS-GDL', name='Operaciones GDL',
            area=cls.area, location=cls.location,
        )
        cls.cost_center_fin = CostCenter.objects.create(
            code='CC-FIN-GDL', name='Finanzas GDL',
            area=cls.area_fin, location=cls.location,
        )
        cls.category = Category.objects.create(
            code=Category.PAPELERIA, name='Papelería',
        )
        cls.category2 = Category.objects.create(
            code=Category.LIMPIEZA, name='Limpieza',
        )

    def _create_user(self, email, role, area=None, cost_center=None):
        return User.objects.create_user(
            username=email.split('@')[0], email=email,
            password='testpass123', first_name='Test', last_name='User',
            role=role, area=area or self.area,
            location=self.location, cost_center=cost_center or self.cost_center,
        )


class CategoryModelTests(BudgetBaseTestCase):

    def test_str_representation(self):
        self.assertEqual(str(self.category), 'Papelería')

    def test_unique_code(self):
        with self.assertRaises(Exception):
            Category.objects.create(code=Category.PAPELERIA, name='Dupe')


class ItemModelTests(BudgetBaseTestCase):

    def test_create_item(self):
        item = Item.objects.create(
            category=self.category, code='PAP-001',
            name='Hojas blancas', unit='Paquete',
        )
        self.assertIn('Papelería', str(item))
        self.assertIn('Hojas blancas', str(item))

    def test_unique_code(self):
        Item.objects.create(category=self.category, code='PAP-X', name='Test')
        with self.assertRaises(Exception):
            Item.objects.create(category=self.category, code='PAP-X', name='Dupe')


class BudgetModelTests(BudgetBaseTestCase):

    def test_create_budget(self):
        budget = Budget.objects.create(
            cost_center=self.cost_center, category=self.category,
            year=2026, month=1, amount=Decimal('50000.00'),
        )
        self.assertEqual(budget.amount, Decimal('50000.00'))
        self.assertFalse(budget.is_closed)

    def test_unique_together(self):
        Budget.objects.create(
            cost_center=self.cost_center, category=self.category,
            year=2026, month=1, amount=Decimal('50000.00'),
        )
        with self.assertRaises(Exception):
            Budget.objects.create(
                cost_center=self.cost_center, category=self.category,
                year=2026, month=1, amount=Decimal('10000.00'),
            )

    def test_get_spent_amount_no_requests(self):
        budget = Budget.objects.create(
            cost_center=self.cost_center, category=self.category,
            year=2026, month=1, amount=Decimal('50000.00'),
        )
        self.assertEqual(budget.get_spent_amount(), Decimal('0.00'))

    def test_get_available_amount(self):
        budget = Budget.objects.create(
            cost_center=self.cost_center, category=self.category,
            year=2026, month=2, amount=Decimal('50000.00'),
        )
        self.assertEqual(budget.get_available_amount(), Decimal('50000.00'))

    def test_utilization_percentage_zero(self):
        budget = Budget.objects.create(
            cost_center=self.cost_center, category=self.category,
            year=2026, month=3, amount=Decimal('50000.00'),
        )
        self.assertEqual(budget.get_utilization_percentage(), 0)

    def test_utilization_percentage_zero_amount(self):
        budget = Budget.objects.create(
            cost_center=self.cost_center, category=self.category,
            year=2026, month=4, amount=Decimal('0.00'),
        )
        self.assertEqual(budget.get_utilization_percentage(), 0)

    def test_is_exceeded(self):
        budget = Budget.objects.create(
            cost_center=self.cost_center, category=self.category,
            year=2026, month=5, amount=Decimal('50000.00'),
        )
        self.assertFalse(budget.is_exceeded())


class BudgetAPITests(BudgetBaseTestCase):
    """Tests de la API de presupuestos."""

    def setUp(self):
        self.client = APIClient()
        self.finance_user = self._create_user(
            'fin@test.com', User.FINANZAS,
            area=self.area_fin, cost_center=self.cost_center_fin,
        )
        self.employee_user = self._create_user('emp@test.com', User.EMPLEADO)
        self.budget = Budget.objects.create(
            cost_center=self.cost_center, category=self.category,
            year=2026, month=1, amount=Decimal('50000.00'),
        )

    def test_list_budgets(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/budgets/budgets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_budget_finance(self):
        self.client.force_authenticate(user=self.finance_user)
        response = self.client.post('/api/budgets/budgets/', {
            'cost_center': self.cost_center.id,
            'category': self.category2.id,
            'year': 2026, 'month': 1,
            'amount': '30000.00',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_budget_employee_denied(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post('/api/budgets/budgets/', {
            'cost_center': self.cost_center.id,
            'category': self.category2.id,
            'year': 2026, 'month': 2,
            'amount': '30000.00',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_budget_records_history(self):
        self.client.force_authenticate(user=self.finance_user)
        response = self.client.patch(
            f'/api/budgets/budgets/{self.budget.id}/',
            {'amount': '60000.00', 'reason': 'Ajuste'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BudgetHistory.objects.count(), 1)
        history = BudgetHistory.objects.first()
        self.assertEqual(history.previous_amount, Decimal('50000.00'))
        self.assertEqual(history.new_amount, Decimal('60000.00'))

    def test_update_closed_budget_denied(self):
        self.budget.is_closed = True
        self.budget.save()
        self.client.force_authenticate(user=self.finance_user)
        response = self.client.patch(
            f'/api/budgets/budgets/{self.budget.id}/',
            {'amount': '60000.00'},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_summary_action(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/budgets/budgets/summary/', {'year': 2026})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_copy_month(self):
        self.client.force_authenticate(user=self.finance_user)
        response = self.client.post('/api/budgets/budgets/copy_month/', {
            'source_year': 2026, 'source_month': 1,
            'target_year': 2026, 'target_month': 2,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['created'], 1)
        self.assertTrue(Budget.objects.filter(year=2026, month=2).exists())

    def test_copy_month_missing_params(self):
        self.client.force_authenticate(user=self.finance_user)
        response = self.client.post('/api/budgets/budgets/copy_month/', {
            'source_year': 2026,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_close_month(self):
        self.client.force_authenticate(user=self.finance_user)
        response = self.client.post('/api/budgets/budgets/close_month/', {
            'year': 2026, 'month': 1,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.budget.refresh_from_db()
        self.assertTrue(self.budget.is_closed)

    def test_reopen_month_finance_only(self):
        self.budget.is_closed = True
        self.budget.save()
        # Employee cannot reopen
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post('/api/budgets/budgets/reopen_month/', {
            'year': 2026, 'month': 1,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Finance can reopen
        self.client.force_authenticate(user=self.finance_user)
        response = self.client.post('/api/budgets/budgets/reopen_month/', {
            'year': 2026, 'month': 1,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.budget.refresh_from_db()
        self.assertFalse(self.budget.is_closed)

    def test_categories_list(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/budgets/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_items_list(self):
        Item.objects.create(category=self.category, code='PAP-001', name='Hojas', unit='Paquete')
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/budgets/items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_budget_history_list(self):
        BudgetHistory.objects.create(
            budget=self.budget, previous_amount=Decimal('50000.00'),
            new_amount=Decimal('60000.00'), changed_by=self.finance_user,
            reason='Test',
        )
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/budgets/budget-history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
