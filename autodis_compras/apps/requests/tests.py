"""
Tests para el módulo de solicitudes de compra.
"""

import datetime
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from autodis_compras.apps.users.models import Area, Location, CostCenter, User
from autodis_compras.apps.budgets.models import Category, Item
from .models import PurchaseRequest, RequestComment, RequestStatusHistory


class RequestBaseTestCase(TestCase):
    """Caso base con datos compartidos."""

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
        cls.category = Category.objects.create(
            code=Category.PAPELERIA, name='Papelería',
        )
        cls.item = Item.objects.create(
            category=cls.category, code='PAP-001',
            name='Hojas blancas', unit='Paquete',
        )

    def _create_user(self, email, role, area=None, cost_center=None):
        return User.objects.create_user(
            username=email.split('@')[0], email=email,
            password='testpass123', first_name='Test', last_name='User',
            role=role, area=area or self.area_ops,
            location=self.location, cost_center=cost_center or self.cost_center,
        )

    def _create_request(self, requester, **kwargs):
        pr = PurchaseRequest.objects.create(
            requester=requester,
            cost_center=kwargs.get('cost_center', requester.cost_center),
            category=kwargs.get('category', self.category),
            description=kwargs.get('description', 'Compra de prueba'),
            estimated_amount=kwargs.get('estimated_amount', Decimal('5000.00')),
            required_date=kwargs.get('required_date', datetime.date(2026, 3, 15)),
            justification=kwargs.get('justification', 'Necesario para operaciones'),
            status=kwargs.get('status', PurchaseRequest.BORRADOR),
        )
        pr.items.add(self.item)
        return pr


class PurchaseRequestModelTests(RequestBaseTestCase):

    def test_auto_request_number(self):
        user = self._create_user('emp@test.com', User.EMPLEADO)
        pr = self._create_request(user)
        self.assertTrue(pr.request_number.startswith('SOL-'))
        self.assertEqual(len(pr.request_number), 15)  # SOL-YYYYMM-XXXX

    def test_auto_cost_center(self):
        user = self._create_user('emp2@test.com', User.EMPLEADO)
        pr = PurchaseRequest.objects.create(
            requester=user,
            category=self.category,
            description='Test',
            estimated_amount=Decimal('1000.00'),
            required_date=datetime.date(2026, 3, 15),
            justification='Test',
        )
        self.assertEqual(pr.cost_center, user.cost_center)

    def test_str_representation(self):
        user = self._create_user('emp3@test.com', User.EMPLEADO)
        pr = self._create_request(user, description='Compra de papelería para oficina central')
        self.assertIn('SOL-', str(pr))
        self.assertIn('Compra de papelería', str(pr))

    def test_can_be_edited_by_requester_only(self):
        emp1 = self._create_user('emp4@test.com', User.EMPLEADO)
        emp2 = self._create_user('emp5@test.com', User.EMPLEADO)
        pr = self._create_request(emp1, status=PurchaseRequest.PENDIENTE_GERENTE)
        self.assertTrue(pr.can_be_edited_by(emp1))
        self.assertFalse(pr.can_be_edited_by(emp2))

    def test_can_be_edited_only_in_pending(self):
        emp = self._create_user('emp6@test.com', User.EMPLEADO)
        pr = self._create_request(emp, status=PurchaseRequest.BORRADOR)
        self.assertFalse(pr.can_be_edited_by(emp))  # Must be PENDIENTE_GERENTE

    def test_can_be_approved_by_manager_same_area(self):
        emp = self._create_user('emp7@test.com', User.EMPLEADO)
        mgr = self._create_user('mgr@test.com', User.GERENTE)
        pr = self._create_request(emp, status=PurchaseRequest.PENDIENTE_GERENTE)
        self.assertTrue(pr.can_be_approved_by_manager(mgr))

    def test_cannot_be_approved_by_manager_different_area(self):
        emp = self._create_user('emp8@test.com', User.EMPLEADO)
        mgr = self._create_user('mgr2@test.com', User.GERENTE, area=self.area_fin, cost_center=self.cost_center_fin)
        pr = self._create_request(emp, status=PurchaseRequest.PENDIENTE_GERENTE)
        self.assertFalse(pr.can_be_approved_by_manager(mgr))

    def test_can_be_approved_by_finance(self):
        emp = self._create_user('emp9@test.com', User.EMPLEADO)
        fin = self._create_user('fin@test.com', User.FINANZAS, area=self.area_fin, cost_center=self.cost_center_fin)
        pr = self._create_request(emp, status=PurchaseRequest.APROBADA_POR_GERENTE)
        self.assertTrue(pr.can_be_approved_by_finance(fin))

    def test_cannot_be_approved_by_finance_wrong_status(self):
        emp = self._create_user('emp10@test.com', User.EMPLEADO)
        fin = self._create_user('fin2@test.com', User.FINANZAS, area=self.area_fin, cost_center=self.cost_center_fin)
        pr = self._create_request(emp, status=PurchaseRequest.PENDIENTE_GERENTE)
        self.assertFalse(pr.can_be_approved_by_finance(fin))


class PurchaseRequestWorkflowAPITests(RequestBaseTestCase):
    """Tests del flujo completo de solicitud via API."""

    def setUp(self):
        self.client = APIClient()
        self.employee = self._create_user('emp@api.com', User.EMPLEADO)
        self.manager = self._create_user('mgr@api.com', User.GERENTE)
        self.finance = self._create_user(
            'fin@api.com', User.FINANZAS,
            area=self.area_fin, cost_center=self.cost_center_fin,
        )

    def test_create_request(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.post('/api/requests/purchase-requests/', {
            'category': self.category.id,
            'items': [self.item.id],
            'description': 'Necesito papel',
            'estimated_amount': '5000.00',
            'required_date': '2026-03-15',
            'justification': 'Para imprimir reportes',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['request_number'].startswith('SOL-'))
        # Auto-set to PENDIENTE_GERENTE
        pr = PurchaseRequest.objects.get(id=response.data['id'])
        self.assertEqual(pr.status, PurchaseRequest.PENDIENTE_GERENTE)
        self.assertEqual(pr.requester, self.employee)

    def test_submit_draft(self):
        pr = self._create_request(self.employee, status=PurchaseRequest.BORRADOR)
        self.client.force_authenticate(user=self.employee)
        response = self.client.post(f'/api/requests/purchase-requests/{pr.id}/submit/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PurchaseRequest.PENDIENTE_GERENTE)

    def test_submit_non_draft_fails(self):
        pr = self._create_request(self.employee, status=PurchaseRequest.PENDIENTE_GERENTE)
        self.client.force_authenticate(user=self.employee)
        response = self.client.post(f'/api/requests/purchase-requests/{pr.id}/submit/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_approve_manager(self):
        pr = self._create_request(self.employee, status=PurchaseRequest.PENDIENTE_GERENTE)
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(f'/api/requests/purchase-requests/{pr.id}/approve_manager/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PurchaseRequest.APROBADA_POR_GERENTE)
        self.assertEqual(pr.manager_approved_by, self.manager)
        self.assertIsNotNone(pr.manager_approved_at)

    def test_approve_manager_wrong_area(self):
        pr = self._create_request(self.employee, status=PurchaseRequest.PENDIENTE_GERENTE)
        other_mgr = self._create_user(
            'mgr2@api.com', User.GERENTE,
            area=self.area_fin, cost_center=self.cost_center_fin,
        )
        self.client.force_authenticate(user=other_mgr)
        response = self.client.post(f'/api/requests/purchase-requests/{pr.id}/approve_manager/')
        # 404 because the request is not in the manager's area queryset
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_approve_final(self):
        pr = self._create_request(self.employee, status=PurchaseRequest.APROBADA_POR_GERENTE)
        self.client.force_authenticate(user=self.finance)
        response = self.client.post(f'/api/requests/purchase-requests/{pr.id}/approve_final/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PurchaseRequest.APROBADA)
        self.assertEqual(pr.final_approved_by, self.finance)

    def test_reject_by_manager(self):
        pr = self._create_request(self.employee, status=PurchaseRequest.PENDIENTE_GERENTE)
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(
            f'/api/requests/purchase-requests/{pr.id}/reject/',
            {'reason': 'No hay presupuesto'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PurchaseRequest.RECHAZADA_GERENTE)
        self.assertEqual(pr.rejection_reason, 'No hay presupuesto')

    def test_reject_without_reason_fails(self):
        pr = self._create_request(self.employee, status=PurchaseRequest.PENDIENTE_GERENTE)
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(f'/api/requests/purchase-requests/{pr.id}/reject/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_by_finance(self):
        pr = self._create_request(self.employee, status=PurchaseRequest.APROBADA_POR_GERENTE)
        self.client.force_authenticate(user=self.finance)
        response = self.client.post(
            f'/api/requests/purchase-requests/{pr.id}/reject/',
            {'reason': 'Excede presupuesto'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PurchaseRequest.RECHAZADA_FINANZAS)

    def test_cancel_by_requester(self):
        pr = self._create_request(self.employee, status=PurchaseRequest.PENDIENTE_GERENTE)
        self.client.force_authenticate(user=self.employee)
        response = self.client.post(f'/api/requests/purchase-requests/{pr.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PurchaseRequest.CANCELADA)

    def test_cancel_by_other_user_fails(self):
        pr = self._create_request(self.employee, status=PurchaseRequest.PENDIENTE_GERENTE)
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(f'/api/requests/purchase-requests/{pr.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_approved_request_fails(self):
        pr = self._create_request(self.employee, status=PurchaseRequest.APROBADA)
        self.client.force_authenticate(user=self.employee)
        response = self.client.post(f'/api/requests/purchase-requests/{pr.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mark_in_process(self):
        pr = self._create_request(self.employee, status=PurchaseRequest.APROBADA)
        self.client.force_authenticate(user=self.finance)
        response = self.client.post(f'/api/requests/purchase-requests/{pr.id}/mark_in_process/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PurchaseRequest.EN_PROCESO)

    def test_mark_in_process_employee_fails(self):
        pr = self._create_request(self.employee, status=PurchaseRequest.APROBADA)
        self.client.force_authenticate(user=self.employee)
        response = self.client.post(f'/api/requests/purchase-requests/{pr.id}/mark_in_process/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mark_purchased(self):
        pr = self._create_request(self.employee, status=PurchaseRequest.EN_PROCESO)
        self.client.force_authenticate(user=self.finance)
        response = self.client.post(f'/api/requests/purchase-requests/{pr.id}/mark_purchased/', {
            'purchase_date': '2026-02-15',
            'actual_supplier': 'Office Depot',
            'actual_amount': '4800.00',
            'invoice_number': 'FAC-001',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PurchaseRequest.COMPRADA)
        self.assertEqual(pr.actual_supplier, 'Office Depot')

    def test_mark_completed(self):
        pr = self._create_request(self.employee, status=PurchaseRequest.COMPRADA)
        self.client.force_authenticate(user=self.finance)
        response = self.client.post(f'/api/requests/purchase-requests/{pr.id}/mark_completed/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PurchaseRequest.COMPLETADA)

    def test_full_workflow(self):
        """Test del flujo completo: crear -> aprobar gerente -> aprobar final -> en proceso -> comprada -> completada."""
        self.client.force_authenticate(user=self.employee)
        # Crear
        response = self.client.post('/api/requests/purchase-requests/', {
            'category': self.category.id,
            'items': [self.item.id],
            'description': 'Flujo completo',
            'estimated_amount': '3000.00',
            'required_date': '2026-03-15',
            'justification': 'Test flujo completo',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pr_id = response.data['id']

        # Aprobar gerente
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(f'/api/requests/purchase-requests/{pr_id}/approve_manager/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Aprobar finanzas
        self.client.force_authenticate(user=self.finance)
        response = self.client.post(f'/api/requests/purchase-requests/{pr_id}/approve_final/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # En proceso
        response = self.client.post(f'/api/requests/purchase-requests/{pr_id}/mark_in_process/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Comprada
        response = self.client.post(f'/api/requests/purchase-requests/{pr_id}/mark_purchased/', {
            'purchase_date': '2026-02-15',
            'actual_supplier': 'Proveedor X',
            'actual_amount': '2800.00',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Completada
        response = self.client.post(f'/api/requests/purchase-requests/{pr_id}/mark_completed/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        pr = PurchaseRequest.objects.get(id=pr_id)
        self.assertEqual(pr.status, PurchaseRequest.COMPLETADA)
        # Should have status history entries
        self.assertEqual(pr.status_history.count(), 5)


class RequestQuerysetFilterTests(RequestBaseTestCase):
    """Tests de filtros de queryset por rol."""

    def setUp(self):
        self.client = APIClient()
        self.employee = self._create_user('emp@qs.com', User.EMPLEADO)
        self.employee2 = self._create_user('emp2@qs.com', User.EMPLEADO)
        self.manager = self._create_user('mgr@qs.com', User.GERENTE)
        self.finance = self._create_user(
            'fin@qs.com', User.FINANZAS,
            area=self.area_fin, cost_center=self.cost_center_fin,
        )
        self.pr1 = self._create_request(self.employee, status=PurchaseRequest.PENDIENTE_GERENTE)
        self.pr2 = self._create_request(self.employee2, status=PurchaseRequest.PENDIENTE_GERENTE)

    def test_employee_sees_own_requests(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/requests/purchase-requests/')
        self.assertEqual(response.data['count'], 1)

    def test_manager_sees_area_requests(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.get('/api/requests/purchase-requests/')
        self.assertEqual(response.data['count'], 2)

    def test_finance_sees_all(self):
        self.client.force_authenticate(user=self.finance)
        response = self.client.get('/api/requests/purchase-requests/')
        self.assertEqual(response.data['count'], 2)


class CommentAPITests(RequestBaseTestCase):
    """Tests de comentarios."""

    def setUp(self):
        self.client = APIClient()
        self.employee = self._create_user('emp@cmt.com', User.EMPLEADO)
        self.pr = self._create_request(self.employee, status=PurchaseRequest.PENDIENTE_GERENTE)

    def test_add_comment(self):
        self.client.force_authenticate(user=self.employee)
        response = self.client.post('/api/requests/comments/', {
            'request': self.pr.id,
            'comment': 'Este es un comentario de prueba.',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RequestComment.objects.count(), 1)

    def test_list_comments_by_request(self):
        RequestComment.objects.create(
            request=self.pr, user=self.employee, comment='Comentario 1',
        )
        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/requests/comments/', {'request': self.pr.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
