"""
Tests end-to-end del flujo completo del Sistema de Compras AUTODIS.
Valida la integridad del flujo: presupuestos, solicitudes, aprobaciones,
rechazos, notificaciones y reportes.
"""

import datetime
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from autodis_compras.apps.users.models import Area, Location, CostCenter, User
from autodis_compras.apps.budgets.models import Category, Item, Budget, BudgetHistory
from autodis_compras.apps.requests.models import (
    PurchaseRequest, RequestComment, RequestStatusHistory,
)
from autodis_compras.apps.notifications.models import EmailNotification


class FullSystemE2ETest(TestCase):
    """
    Test end-to-end del sistema completo.
    Simula un mes de operación con múltiples usuarios, solicitudes,
    presupuestos y el ciclo de vida completo.
    """

    @classmethod
    def setUpTestData(cls):
        # Crear áreas
        cls.area_ops = Area.objects.create(name=Area.OPERACIONES)
        cls.area_com = Area.objects.create(name=Area.COMERCIAL)
        cls.area_fin = Area.objects.create(name=Area.FINANZAS)

        # Crear ubicaciones
        cls.loc_gdl = Location.objects.create(name=Location.GUADALAJARA)
        cls.loc_cul = Location.objects.create(name=Location.CULIACAN)

        # Crear centros de costos
        cls.cc_ops_gdl = CostCenter.objects.create(
            code='CC-OPS-GDL', name='Operaciones Guadalajara',
            area=cls.area_ops, location=cls.loc_gdl,
        )
        cls.cc_com_gdl = CostCenter.objects.create(
            code='CC-COM-GDL', name='Comercial Guadalajara',
            area=cls.area_com, location=cls.loc_gdl,
        )
        cls.cc_fin_gdl = CostCenter.objects.create(
            code='CC-FIN-GDL', name='Finanzas Guadalajara',
            area=cls.area_fin, location=cls.loc_gdl,
        )

        # Crear categorías e items
        cls.cat_pap = Category.objects.create(code=Category.PAPELERIA, name='Papelería')
        cls.cat_lim = Category.objects.create(code=Category.LIMPIEZA, name='Limpieza')
        cls.item_hojas = Item.objects.create(
            category=cls.cat_pap, code='PAP-001', name='Hojas blancas', unit='Paquete',
        )
        cls.item_toner = Item.objects.create(
            category=cls.cat_pap, code='PAP-002', name='Tóner impresora', unit='Pieza',
        )
        cls.item_jabon = Item.objects.create(
            category=cls.cat_lim, code='LIM-001', name='Jabón líquido', unit='Litro',
        )

    def setUp(self):
        self.client = APIClient()
        now = timezone.now()

        # Crear usuarios
        self.emp_ops = self._create_user('juan.lopez@autodis.mx', User.EMPLEADO,
                                          'Juan', 'Lopez', self.area_ops, self.cc_ops_gdl)
        self.emp_com = self._create_user('maria.garcia@autodis.mx', User.EMPLEADO,
                                          'Maria', 'Garcia', self.area_com, self.cc_com_gdl)
        self.mgr_ops = self._create_user('carlos.ramirez@autodis.mx', User.GERENTE,
                                          'Carlos', 'Ramirez', self.area_ops, self.cc_ops_gdl)
        self.mgr_com = self._create_user('ana.martinez@autodis.mx', User.GERENTE,
                                          'Ana', 'Martinez', self.area_com, self.cc_com_gdl)
        self.finance = self._create_user('pedro.finanzas@autodis.mx', User.FINANZAS,
                                          'Pedro', 'Finanzas', self.area_fin, self.cc_fin_gdl)
        self.director = self._create_user('director@autodis.mx', User.DIRECCION_GENERAL,
                                           'Roberto', 'Director', self.area_fin, self.cc_fin_gdl)

        # Crear presupuestos para el mes actual
        self.budget_ops_pap = Budget.objects.create(
            cost_center=self.cc_ops_gdl, category=self.cat_pap,
            year=now.year, month=now.month, amount=Decimal('50000.00'),
        )
        self.budget_com_pap = Budget.objects.create(
            cost_center=self.cc_com_gdl, category=self.cat_pap,
            year=now.year, month=now.month, amount=Decimal('30000.00'),
        )
        self.budget_ops_lim = Budget.objects.create(
            cost_center=self.cc_ops_gdl, category=self.cat_lim,
            year=now.year, month=now.month, amount=Decimal('20000.00'),
        )

    def _create_user(self, email, role, first_name, last_name, area, cost_center):
        return User.objects.create_user(
            username=email.split('@')[0], email=email,
            password='SecurePass123!', first_name=first_name,
            last_name=last_name, role=role, area=area,
            location=self.loc_gdl, cost_center=cost_center,
        )

    def test_e2e_complete_purchase_workflow(self):
        """
        Flujo feliz completo:
        1. Empleado crea solicitud
        2. Gerente aprueba
        3. Finanzas aprueba
        4. Se marca en proceso
        5. Se registra la compra
        6. Se marca como completada
        """
        # 1. Empleado de Operaciones crea solicitud de papelería
        self.client.force_authenticate(user=self.emp_ops)
        response = self.client.post('/api/requests/purchase-requests/', {
            'category': self.cat_pap.id,
            'items': [self.item_hojas.id, self.item_toner.id],
            'description': 'Compra mensual de papelería para oficina',
            'estimated_amount': '15000.00',
            'required_date': '2026-03-01',
            'justification': 'Suministro mensual necesario para operaciones',
            'urgency': 'NORMAL',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pr_id = response.data['id']
        pr_number = response.data['request_number']
        self.assertTrue(pr_number.startswith('SOL-'))

        # Verificar que el presupuesto no se excede
        pr = PurchaseRequest.objects.get(id=pr_id)
        self.assertEqual(pr.status, PurchaseRequest.PENDIENTE_GERENTE)
        self.assertEqual(pr.requester, self.emp_ops)
        self.assertEqual(pr.cost_center, self.cc_ops_gdl)

        # 2. Gerente de Operaciones aprueba
        self.client.force_authenticate(user=self.mgr_ops)
        response = self.client.post(
            f'/api/requests/purchase-requests/{pr_id}/approve_manager/',
            {'notes': 'Aprobado, es compra recurrente'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PurchaseRequest.APROBADA_POR_GERENTE)
        self.assertEqual(pr.manager_approved_by, self.mgr_ops)

        # 3. Finanzas aprueba
        self.client.force_authenticate(user=self.finance)
        response = self.client.post(
            f'/api/requests/purchase-requests/{pr_id}/approve_final/',
            {'notes': 'Dentro del presupuesto'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PurchaseRequest.APROBADA)
        self.assertEqual(pr.final_approved_by, self.finance)

        # 4. Finanzas marca en proceso
        response = self.client.post(f'/api/requests/purchase-requests/{pr_id}/mark_in_process/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PurchaseRequest.EN_PROCESO)

        # 5. Se registra la compra
        response = self.client.post(f'/api/requests/purchase-requests/{pr_id}/mark_purchased/', {
            'purchase_date': '2026-02-15',
            'actual_supplier': 'Office Depot',
            'actual_amount': '14500.00',
            'invoice_number': 'FAC-2026-0042',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PurchaseRequest.COMPRADA)
        self.assertEqual(pr.actual_supplier, 'Office Depot')
        self.assertEqual(pr.actual_amount, Decimal('14500.00'))

        # 6. Se marca como completada
        response = self.client.post(f'/api/requests/purchase-requests/{pr_id}/mark_completed/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pr.refresh_from_db()
        self.assertEqual(pr.status, PurchaseRequest.COMPLETADA)

        # Verificar historial de estados completo
        history = RequestStatusHistory.objects.filter(request=pr).order_by('created_at')
        self.assertEqual(history.count(), 5)
        states = list(history.values_list('new_status', flat=True))
        self.assertEqual(states, [
            PurchaseRequest.APROBADA_POR_GERENTE,
            PurchaseRequest.APROBADA,
            PurchaseRequest.EN_PROCESO,
            PurchaseRequest.COMPRADA,
            PurchaseRequest.COMPLETADA,
        ])

    def test_e2e_rejection_workflow(self):
        """
        Flujo de rechazo:
        1. Empleado crea solicitud
        2. Gerente rechaza con motivo
        3. Se verifica el estado y motivo
        """
        self.client.force_authenticate(user=self.emp_com)
        response = self.client.post('/api/requests/purchase-requests/', {
            'category': self.cat_pap.id,
            'items': [self.item_hojas.id],
            'description': 'Compra de papelería premium',
            'estimated_amount': '25000.00',
            'required_date': '2026-03-01',
            'justification': 'Quiero papel especial',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pr_id = response.data['id']

        # Gerente comercial rechaza
        self.client.force_authenticate(user=self.mgr_com)
        response = self.client.post(f'/api/requests/purchase-requests/{pr_id}/reject/', {
            'reason': 'El monto es excesivo para papelería. Usar proveedor estándar.',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        pr = PurchaseRequest.objects.get(id=pr_id)
        self.assertEqual(pr.status, PurchaseRequest.RECHAZADA_GERENTE)
        self.assertEqual(pr.rejection_reason, 'El monto es excesivo para papelería. Usar proveedor estándar.')
        self.assertEqual(pr.rejected_by, self.mgr_com)

    def test_e2e_budget_tracking(self):
        """
        Verifica que el presupuesto se actualiza correctamente
        al aprobar solicitudes.
        """
        # Verificar presupuesto inicial
        self.assertEqual(self.budget_ops_pap.get_spent_amount(), Decimal('0.00'))
        self.assertEqual(self.budget_ops_pap.get_available_amount(), Decimal('50000.00'))

        # Crear y aprobar solicitud
        self.client.force_authenticate(user=self.emp_ops)
        response = self.client.post('/api/requests/purchase-requests/', {
            'category': self.cat_pap.id,
            'items': [self.item_hojas.id],
            'description': 'Primera compra',
            'estimated_amount': '20000.00',
            'required_date': '2026-03-01',
            'justification': 'Necesaria',
        })
        pr_id = response.data['id']

        # Aprobar gerente
        self.client.force_authenticate(user=self.mgr_ops)
        self.client.post(f'/api/requests/purchase-requests/{pr_id}/approve_manager/')

        # Verificar presupuesto gastado (aprobada por gerente cuenta como gasto)
        self.budget_ops_pap.refresh_from_db()
        self.assertEqual(self.budget_ops_pap.get_spent_amount(), Decimal('20000.00'))
        self.assertEqual(self.budget_ops_pap.get_available_amount(), Decimal('30000.00'))
        self.assertEqual(self.budget_ops_pap.get_utilization_percentage(), 40)
        self.assertFalse(self.budget_ops_pap.is_exceeded())

    def test_e2e_budget_exceeded(self):
        """
        Verifica que se detecta cuando una solicitud excede el presupuesto.
        """
        self.client.force_authenticate(user=self.emp_ops)
        response = self.client.post('/api/requests/purchase-requests/', {
            'category': self.cat_pap.id,
            'items': [self.item_hojas.id],
            'description': 'Compra grande',
            'estimated_amount': '60000.00',
            'required_date': '2026-03-01',
            'justification': 'Es urgente',
            'budget_excess_justification': 'Se necesita un volumen mayor este mes',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        pr = PurchaseRequest.objects.get(id=response.data['id'])
        # check_budget_excess is called during creation
        pr.check_budget_excess()
        self.assertTrue(pr.exceeds_budget)

    def test_e2e_role_based_visibility(self):
        """
        Verifica que cada rol solo ve las solicitudes que le corresponden.
        """
        # Crear solicitudes para diferentes áreas
        self.client.force_authenticate(user=self.emp_ops)
        self.client.post('/api/requests/purchase-requests/', {
            'category': self.cat_pap.id, 'items': [self.item_hojas.id],
            'description': 'Solicitud Ops', 'estimated_amount': '5000.00',
            'required_date': '2026-03-01', 'justification': 'Test',
        })

        self.client.force_authenticate(user=self.emp_com)
        self.client.post('/api/requests/purchase-requests/', {
            'category': self.cat_pap.id, 'items': [self.item_hojas.id],
            'description': 'Solicitud Comercial', 'estimated_amount': '3000.00',
            'required_date': '2026-03-01', 'justification': 'Test',
        })

        # Empleado Ops solo ve la suya
        self.client.force_authenticate(user=self.emp_ops)
        response = self.client.get('/api/requests/purchase-requests/')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['description'], 'Solicitud Ops')

        # Gerente Ops ve las de su área
        self.client.force_authenticate(user=self.mgr_ops)
        response = self.client.get('/api/requests/purchase-requests/')
        self.assertEqual(response.data['count'], 1)

        # Gerente Comercial ve las de su área
        self.client.force_authenticate(user=self.mgr_com)
        response = self.client.get('/api/requests/purchase-requests/')
        self.assertEqual(response.data['count'], 1)

        # Finanzas ve todas
        self.client.force_authenticate(user=self.finance)
        response = self.client.get('/api/requests/purchase-requests/')
        self.assertEqual(response.data['count'], 2)

        # Director General ve todas
        self.client.force_authenticate(user=self.director)
        response = self.client.get('/api/requests/purchase-requests/')
        self.assertEqual(response.data['count'], 2)

    def test_e2e_comments_workflow(self):
        """
        Verifica que los comentarios se agregan correctamente durante el flujo.
        """
        # Crear solicitud
        self.client.force_authenticate(user=self.emp_ops)
        response = self.client.post('/api/requests/purchase-requests/', {
            'category': self.cat_pap.id, 'items': [self.item_hojas.id],
            'description': 'Solicitud con comentarios',
            'estimated_amount': '5000.00', 'required_date': '2026-03-01',
            'justification': 'Test',
        })
        pr_id = response.data['id']

        # Empleado agrega comentario
        response = self.client.post('/api/requests/comments/', {
            'request': pr_id,
            'comment': 'El proveedor sugerido es Office Depot.',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Gerente agrega comentario
        self.client.force_authenticate(user=self.mgr_ops)
        response = self.client.post('/api/requests/comments/', {
            'request': pr_id,
            'comment': 'Favor de incluir cotización.',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verificar comentarios
        self.client.force_authenticate(user=self.emp_ops)
        response = self.client.get('/api/requests/comments/', {'request': pr_id})
        self.assertEqual(response.data['count'], 2)

    def test_e2e_budget_management(self):
        """
        Verifica la gestión avanzada de presupuestos: copiar mes, cerrar, reabrir.
        """
        now = timezone.now()

        # Copiar presupuestos al mes siguiente
        self.client.force_authenticate(user=self.finance)
        next_month = now.month + 1 if now.month < 12 else 1
        next_year = now.year if now.month < 12 else now.year + 1
        response = self.client.post('/api/budgets/budgets/copy_month/', {
            'source_year': now.year, 'source_month': now.month,
            'target_year': next_year, 'target_month': next_month,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['created'], 3)  # 3 presupuestos copiados

        # Verificar que se crearon
        copied = Budget.objects.filter(year=next_year, month=next_month)
        self.assertEqual(copied.count(), 3)

        # Cerrar el mes actual
        response = self.client.post('/api/budgets/budgets/close_month/', {
            'year': now.year, 'month': now.month,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['closed'], 3)

        # Verificar que están cerrados
        self.budget_ops_pap.refresh_from_db()
        self.assertTrue(self.budget_ops_pap.is_closed)

        # Intentar modificar presupuesto cerrado debe fallar
        response = self.client.patch(
            f'/api/budgets/budgets/{self.budget_ops_pap.id}/',
            {'amount': '60000.00'},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Reabrir el mes
        response = self.client.post('/api/budgets/budgets/reopen_month/', {
            'year': now.year, 'month': now.month,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.budget_ops_pap.refresh_from_db()
        self.assertFalse(self.budget_ops_pap.is_closed)

    def test_e2e_reports(self):
        """
        Verifica que los reportes devuelven datos correctos.
        """
        now = timezone.now()

        # Crear solicitud aprobada
        self.client.force_authenticate(user=self.emp_ops)
        response = self.client.post('/api/requests/purchase-requests/', {
            'category': self.cat_pap.id, 'items': [self.item_hojas.id],
            'description': 'Para reporte', 'estimated_amount': '10000.00',
            'required_date': '2026-03-01', 'justification': 'Test reportes',
        })
        pr_id = response.data['id']

        # Aprobar gerente
        self.client.force_authenticate(user=self.mgr_ops)
        self.client.post(f'/api/requests/purchase-requests/{pr_id}/approve_manager/')

        # Aprobar finanzas
        self.client.force_authenticate(user=self.finance)
        self.client.post(f'/api/requests/purchase-requests/{pr_id}/approve_final/')

        # Verificar reporte de gastos por periodo
        response = self.client.get('/api/reports/expenses-by-period/', {
            'year': now.year, 'month': now.month,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data['totals']['total_count'], 0)

        # Verificar comparativo de presupuesto
        response = self.client.get('/api/reports/budget-comparison/', {
            'year': now.year, 'month': now.month,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) > 0)

        # Verificar dashboard
        response = self.client.get('/api/reports/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('pending_manager_approval', response.data)
        self.assertIn('monthly_spend', response.data)

    def test_e2e_cancellation(self):
        """
        Verifica que un empleado puede cancelar su propia solicitud.
        """
        self.client.force_authenticate(user=self.emp_ops)
        response = self.client.post('/api/requests/purchase-requests/', {
            'category': self.cat_pap.id, 'items': [self.item_hojas.id],
            'description': 'Solicitud a cancelar', 'estimated_amount': '5000.00',
            'required_date': '2026-03-01', 'justification': 'Test',
        })
        pr_id = response.data['id']

        # Cancelar
        response = self.client.post(f'/api/requests/purchase-requests/{pr_id}/cancel/', {
            'notes': 'Ya no se necesita',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        pr = PurchaseRequest.objects.get(id=pr_id)
        self.assertEqual(pr.status, PurchaseRequest.CANCELADA)

    def test_e2e_finance_rejection(self):
        """
        Flujo donde gerente aprueba pero finanzas rechaza.
        """
        self.client.force_authenticate(user=self.emp_ops)
        response = self.client.post('/api/requests/purchase-requests/', {
            'category': self.cat_pap.id, 'items': [self.item_hojas.id],
            'description': 'Será rechazada por finanzas',
            'estimated_amount': '45000.00', 'required_date': '2026-03-01',
            'justification': 'Test rechazo finanzas',
        })
        pr_id = response.data['id']

        # Gerente aprueba
        self.client.force_authenticate(user=self.mgr_ops)
        self.client.post(f'/api/requests/purchase-requests/{pr_id}/approve_manager/')

        # Finanzas rechaza
        self.client.force_authenticate(user=self.finance)
        response = self.client.post(f'/api/requests/purchase-requests/{pr_id}/reject/', {
            'reason': 'Excede el presupuesto mensual permitido. Dividir en 2 meses.',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        pr = PurchaseRequest.objects.get(id=pr_id)
        self.assertEqual(pr.status, PurchaseRequest.RECHAZADA_FINANZAS)
        self.assertEqual(pr.rejected_by, self.finance)

        # Verificar historial completo
        history = RequestStatusHistory.objects.filter(request=pr).order_by('created_at')
        self.assertEqual(history.count(), 2)

    def test_e2e_director_can_also_approve(self):
        """
        Verifica que el Director General también puede dar aprobación final.
        """
        self.client.force_authenticate(user=self.emp_ops)
        response = self.client.post('/api/requests/purchase-requests/', {
            'category': self.cat_lim.id, 'items': [self.item_jabon.id],
            'description': 'Compra de limpieza',
            'estimated_amount': '8000.00', 'required_date': '2026-03-01',
            'justification': 'Suministro mensual',
        })
        pr_id = response.data['id']

        # Gerente aprueba
        self.client.force_authenticate(user=self.mgr_ops)
        self.client.post(f'/api/requests/purchase-requests/{pr_id}/approve_manager/')

        # Director General da aprobación final
        self.client.force_authenticate(user=self.director)
        response = self.client.post(f'/api/requests/purchase-requests/{pr_id}/approve_final/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        pr = PurchaseRequest.objects.get(id=pr_id)
        self.assertEqual(pr.status, PurchaseRequest.APROBADA)
        self.assertEqual(pr.final_approved_by, self.director)

    def test_e2e_multiple_requests_budget_accumulation(self):
        """
        Verifica que múltiples solicitudes acumulan correctamente el gasto.
        """
        now = timezone.now()

        # Crear y aprobar 3 solicitudes
        amounts = [Decimal('10000'), Decimal('15000'), Decimal('8000')]
        for i, amount in enumerate(amounts):
            self.client.force_authenticate(user=self.emp_ops)
            response = self.client.post('/api/requests/purchase-requests/', {
                'category': self.cat_pap.id, 'items': [self.item_hojas.id],
                'description': f'Compra {i+1}',
                'estimated_amount': str(amount), 'required_date': '2026-03-01',
                'justification': 'Test acumulación',
            })
            pr_id = response.data['id']

            self.client.force_authenticate(user=self.mgr_ops)
            self.client.post(f'/api/requests/purchase-requests/{pr_id}/approve_manager/')

        # Verificar presupuesto acumulado
        self.budget_ops_pap.refresh_from_db()
        expected_spent = sum(amounts)
        self.assertEqual(self.budget_ops_pap.get_spent_amount(), expected_spent)
        self.assertEqual(
            self.budget_ops_pap.get_available_amount(),
            Decimal('50000.00') - expected_spent,
        )
        self.assertFalse(self.budget_ops_pap.is_exceeded())
