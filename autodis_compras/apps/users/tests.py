"""
Tests para el módulo de usuarios.
"""

import datetime
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from .models import Area, Location, CostCenter, User


class BaseTestCase(TestCase):
    """Caso base con datos compartidos para todos los tests."""

    @classmethod
    def setUpTestData(cls):
        cls.area_ops = Area.objects.create(name=Area.OPERACIONES)
        cls.area_fin = Area.objects.create(name=Area.FINANZAS)
        cls.location = Location.objects.create(name=Location.GUADALAJARA)
        cls.cost_center = CostCenter.objects.create(
            code='CC-OPS-GDL', name='Operaciones GDL',
            area=cls.area_ops, location=cls.location,
        )
        cls.cost_center_fin = CostCenter.objects.create(
            code='CC-FIN-GDL', name='Finanzas GDL',
            area=cls.area_fin, location=cls.location,
        )

    def _create_user(self, email, role, area=None, cost_center=None, **kwargs):
        return User.objects.create_user(
            username=email.split('@')[0],
            email=email,
            password='testpass123',
            first_name=kwargs.get('first_name', 'Test'),
            last_name=kwargs.get('last_name', 'User'),
            role=role,
            area=area or self.area_ops,
            location=self.location,
            cost_center=cost_center or self.cost_center,
        )


class UserModelTests(BaseTestCase):
    """Tests del modelo User."""

    def test_email_lowercase_on_save(self):
        user = self._create_user('UPPER@EXAMPLE.COM', User.EMPLEADO)
        self.assertEqual(user.email, 'upper@example.com')

    def test_str_representation(self):
        user = self._create_user('str@test.com', User.GERENTE, first_name='Juan', last_name='Perez')
        self.assertIn('Juan Perez', str(user))
        self.assertIn('Gerente', str(user))

    def test_is_manager(self):
        manager = self._create_user('mgr@test.com', User.GERENTE)
        employee = self._create_user('emp@test.com', User.EMPLEADO)
        self.assertTrue(manager.is_manager())
        self.assertFalse(employee.is_manager())

    def test_is_finance(self):
        fin = self._create_user('fin@test.com', User.FINANZAS, area=self.area_fin, cost_center=self.cost_center_fin)
        self.assertTrue(fin.is_finance())

    def test_is_general_director(self):
        dg = self._create_user('dg@test.com', User.DIRECCION_GENERAL)
        self.assertTrue(dg.is_general_director())

    def test_is_approver(self):
        emp = self._create_user('emp2@test.com', User.EMPLEADO)
        mgr = self._create_user('mgr2@test.com', User.GERENTE)
        fin = self._create_user('fin2@test.com', User.FINANZAS, area=self.area_fin, cost_center=self.cost_center_fin)
        dg = self._create_user('dg2@test.com', User.DIRECCION_GENERAL)
        self.assertFalse(emp.is_approver())
        self.assertTrue(mgr.is_approver())
        self.assertTrue(fin.is_approver())
        self.assertTrue(dg.is_approver())

    def test_can_manage_users(self):
        emp = self._create_user('emp3@test.com', User.EMPLEADO)
        mgr = self._create_user('mgr3@test.com', User.GERENTE)
        self.assertFalse(emp.can_manage_users())
        self.assertTrue(mgr.can_manage_users())

    def test_can_manage_budgets(self):
        mgr = self._create_user('mgr4@test.com', User.GERENTE)
        fin = self._create_user('fin4@test.com', User.FINANZAS, area=self.area_fin, cost_center=self.cost_center_fin)
        self.assertFalse(mgr.can_manage_budgets())
        self.assertTrue(fin.can_manage_budgets())


class AreaModelTests(BaseTestCase):

    def test_str_display(self):
        self.assertEqual(str(self.area_ops), 'Operaciones')

    def test_unique_name(self):
        with self.assertRaises(Exception):
            Area.objects.create(name=Area.OPERACIONES)


class LocationModelTests(BaseTestCase):

    def test_str_display(self):
        self.assertEqual(str(self.location), 'Guadalajara')


class CostCenterModelTests(BaseTestCase):

    def test_str_display(self):
        self.assertIn('CC-OPS-GDL', str(self.cost_center))

    def test_unique_code(self):
        with self.assertRaises(Exception):
            CostCenter.objects.create(
                code='CC-OPS-GDL', name='Duplicado',
                area=self.area_ops, location=self.location,
            )


class UserAPITests(BaseTestCase):
    """Tests de los endpoints de la API de usuarios."""

    def setUp(self):
        self.client = APIClient()
        self.finance_user = self._create_user(
            'finance@test.com', User.FINANZAS,
            area=self.area_fin, cost_center=self.cost_center_fin,
        )
        self.manager_user = self._create_user('manager@test.com', User.GERENTE)
        self.employee_user = self._create_user('employee@test.com', User.EMPLEADO)

    def test_unauthenticated_access_denied(self):
        response = self.client.get('/api/users/users/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_finance_sees_all_users(self):
        self.client.force_authenticate(user=self.finance_user)
        response = self.client.get('/api/users/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_manager_sees_area_users(self):
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.get('/api/users/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Manager and employee are in area_ops
        self.assertEqual(response.data['count'], 2)

    def test_employee_sees_only_self(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/users/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_me_endpoint(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/users/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'employee@test.com')

    def test_me_endpoint_patch(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.patch('/api/users/users/me/', {'phone': '3312345678'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee_user.refresh_from_db()
        self.assertEqual(self.employee_user.phone, '3312345678')

    def test_employee_cannot_create_user(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post('/api/users/users/', {
            'email': 'new@test.com', 'username': 'newuser',
            'first_name': 'New', 'last_name': 'User',
            'password': 'testpass123', 'role': User.EMPLEADO,
            'area': self.area_ops.id, 'location': self.location.id,
            'cost_center': self.cost_center.id,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_finance_can_create_user(self):
        self.client.force_authenticate(user=self.finance_user)
        response = self.client.post('/api/users/users/', {
            'email': 'new@test.com', 'username': 'newuser',
            'first_name': 'New', 'last_name': 'User',
            'password': 'testpass123', 'role': User.EMPLEADO,
            'area': self.area_ops.id, 'location': self.location.id,
            'cost_center': self.cost_center.id,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_areas_list(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/users/areas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_locations_list(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/users/locations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_cost_centers_list(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get('/api/users/cost-centers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)



# NOTE: JWT auth tests are skipped in this environment due to a cryptography
# library incompatibility (pyo3_runtime.PanicException). They should be run
# in a properly configured environment with PyJWT and cryptography installed.
