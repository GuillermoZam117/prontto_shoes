"""
Pruebas automáticas para el endpoint de logs de auditoría:
- Creación de log
- Listado de logs
- Filtrado por acción
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import LogAuditoria
from django.contrib.auth import get_user_model

class LogAuditoriaAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.log_data = {
            'usuario': self.user.id,
            'accion': 'CREAR',
            'descripcion': 'Creación de registro'
        }

    def test_create_log(self):
        url = reverse('logauditoria-list')
        response = self.client.post(url, self.log_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LogAuditoria.objects.count(), 1)
        self.assertEqual(LogAuditoria.objects.get().accion, 'CREAR')

    def test_list_logs(self):
        LogAuditoria.objects.create(usuario=self.user, accion='CREAR', descripcion='Creación de registro')
        url = reverse('logauditoria-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_log_by_accion(self):
        LogAuditoria.objects.create(usuario=self.user, accion='CREAR', descripcion='Creación de registro')
        url = reverse('logauditoria-list') + '?accion=CREAR'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['accion'], 'CREAR')
