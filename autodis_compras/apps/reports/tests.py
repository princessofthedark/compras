"""
Tests para el módulo de reportes.
"""

import datetime
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from autodis_compras.apps.users.models import Area, Location, CostCenter, User
from autodis_compras.apps.budgets.models import Category, Item, Budget
from autodis_compras.apps.requests.models import PurchaseRequest


class ReportBaseTestCase(TestCase):

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
        cls.category = Category.objects.create(code=Category.PAPELERIA, name='Papelería')
        cls.item = Item.objects.create(category=cls.category, code='PAP-001', name='Hojas', unit='Paquete')

    def _create_user(self, email, role, area=None, cost_center=None):
        return User.objects.create_user(
            username=email.split('@')[0], email=email,
            password='testpass123', first_name='Test', last_name='User',
            role=role, area=area or self.area,
            location=self.location, cost_center=cost_center or self.cost_center,
        )

    def _create_approved_request(self, requester, amount='5000.00'):
        pr = PurchaseRequest.objects.create(
            requester=requester, cost_center=requester.cost_center,
            category=self.category, description='Compra de prueba',
            estimated_amount=Decimal(amount),
            required_date=datetime.date(2026, 3, 15),
            justification='Test', status=PurchaseRequest.APROBADA,
        )
        pr.items.add(self.item)
        return pr


class ExpensesByPeriodTests(ReportBaseTestCase):

    def setUp(self):
        self.client = APIClient()
        self.employee = self._create_user('emp@rpt.com', User.EMPLEADO)
        self._create_approved_request(self.employee)

    def test_requires_year(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/reports/expenses-by-period/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_json_response(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/reports/expenses-by-period/', {'year': 2026})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('totals', response.data)
        self.assertIn('by_category', response.data)
        self.assertIn('by_cost_center', response.data)

    def test_export_excel(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/reports/expenses-by-period/', {'year': 2026, 'export': 'excel'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('spreadsheetml', response['Content-Type'])

    def test_export_pdf(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/reports/expenses-by-period/', {'year': 2026, 'export': 'pdf'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')


class BudgetComparisonTests(ReportBaseTestCase):

    def setUp(self):
        self.client = APIClient()
        self.employee = self._create_user('emp@bgt.com', User.EMPLEADO)
        now = datetime.datetime.now()
        Budget.objects.create(
            cost_center=self.cost_center, category=self.category,
            year=now.year, month=now.month, amount=Decimal('50000.00'),
        )

    def test_requires_year(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/reports/budget-comparison/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_json_response(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/reports/budget-comparison/', {'year': 2026})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertTrue(len(response.data['results']) > 0)

    def test_export_excel(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/reports/budget-comparison/', {'year': 2026, 'export': 'excel'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('spreadsheetml', response['Content-Type'])

    def test_export_pdf(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/reports/budget-comparison/', {'year': 2026, 'export': 'pdf'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')


class ExpensesByEmployeeTests(ReportBaseTestCase):

    def setUp(self):
        self.client = APIClient()
        self.employee = self._create_user('emp@emprpt.com', User.EMPLEADO)
        self._create_approved_request(self.employee)

    def test_json_response(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/reports/expenses-by-employee/', {'year': 2026})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_export_excel(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/reports/expenses-by-employee/', {'year': 2026, 'export': 'excel'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('spreadsheetml', response['Content-Type'])


class TopSuppliersTests(ReportBaseTestCase):

    def setUp(self):
        self.client = APIClient()
        self.employee = self._create_user('emp@sup.com', User.EMPLEADO)
        pr = PurchaseRequest.objects.create(
            requester=self.employee, cost_center=self.cost_center,
            category=self.category, description='Compra completada',
            estimated_amount=Decimal('5000.00'),
            required_date=datetime.date(2026, 3, 15),
            justification='Test', status=PurchaseRequest.COMPLETADA,
            actual_supplier='Office Depot', actual_amount=Decimal('4800.00'),
        )
        pr.items.add(self.item)

    def test_json_response(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/reports/top-suppliers/', {'year': 2026})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['actual_supplier'], 'Office Depot')


class DashboardTests(ReportBaseTestCase):

    def setUp(self):
        self.client = APIClient()
        self.employee = self._create_user('emp@dash.com', User.EMPLEADO)
        self.finance = self._create_user(
            'fin@dash.com', User.FINANZAS,
            area=self.area_fin, cost_center=self.cost_center_fin,
        )
        self._create_approved_request(self.employee)

    def test_employee_dashboard(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/reports/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('pending_manager_approval', response.data)
        self.assertIn('monthly_spend', response.data)

    def test_finance_dashboard(self):
        self.client.force_authenticate(user=self.finance)
        response = self.client.get('/api/reports/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        response = self.client.get('/api/reports/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
