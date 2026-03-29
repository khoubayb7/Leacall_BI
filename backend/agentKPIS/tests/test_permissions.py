from unittest.mock import Mock, patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ETL.models import ClientDataSource
from agentKPIS.models import KPIExecution
from user.models import CustomUser


class KpiPermissionTests(APITestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username="admin_kpi",
            email="admin_kpi@example.com",
            password="secret123",
            role=CustomUser.Role.ADMIN,
        )
        self.client_a = CustomUser.objects.create_user(
            username="client_a",
            email="client_a@example.com",
            password="secret123",
            role=CustomUser.Role.CLIENT,
        )
        self.client_b = CustomUser.objects.create_user(
            username="client_b",
            email="client_b@example.com",
            password="secret123",
            role=CustomUser.Role.CLIENT,
        )

        self.ds_a = ClientDataSource.objects.create(
            client=self.client_a,
            campaign_id="cmp-a",
            campaign_name="Campaign A",
            campaign_type="leacall_campaign",
            is_active=True,
        )
        self.ds_b = ClientDataSource.objects.create(
            client=self.client_b,
            campaign_id="cmp-b",
            campaign_name="Campaign B",
            campaign_type="leacall_campaign",
            is_active=True,
        )

        self.exec_a = KPIExecution.objects.create(
            ask="AUTO_INTERNAL_PROMPT",
            client=self.client_a,
            campaign_id="cmp-a",
            campaign_name="Campaign A",
            campaign_type="leacall_campaign",
            file_path="/tmp/kpi_a.py",
            status="success",
            celery_task_id="task-a",
        )
        self.exec_b = KPIExecution.objects.create(
            ask="AUTO_INTERNAL_PROMPT",
            client=self.client_b,
            campaign_id="cmp-b",
            campaign_name="Campaign B",
            campaign_type="leacall_campaign",
            file_path="/tmp/kpi_b.py",
            status="success",
            celery_task_id="task-b",
        )

    def test_kpi_endpoints_require_authentication(self):
        response_list = self.client.get(reverse("kpi-execution-list"))
        response_generate = self.client.post(reverse("kpi-generate"), {"campaign_id": "cmp-a"}, format="json")

        self.assertEqual(response_list.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response_generate.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_cannot_access_other_account_execution_detail(self):
        self.client.force_authenticate(user=self.client_a)

        response = self.client.get(reverse("kpi-execution-detail", kwargs={"execution_id": self.exec_b.id}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_admin_list_only_returns_own_executions(self):
        self.client.force_authenticate(user=self.client_a)

        response = self.client.get(reverse("kpi-execution-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.exec_a.id)

    def test_non_admin_cannot_generate_kpi_for_other_account_campaign(self):
        self.client.force_authenticate(user=self.client_a)

        response = self.client.post(
            reverse("kpi-generate"),
            {"campaign_id": "cmp-b", "campaign_name": "Campaign B"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_access_all_kpi_data(self):
        self.client.force_authenticate(user=self.admin)

        response_list = self.client.get(reverse("kpi-execution-list"))
        response_detail = self.client.get(reverse("kpi-execution-detail", kwargs={"execution_id": self.exec_b.id}))

        self.assertEqual(response_list.status_code, status.HTTP_200_OK)
        self.assertEqual(response_list.data["count"], 2)
        self.assertEqual(response_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(response_detail.data["id"], self.exec_b.id)

    def test_non_admin_cannot_access_other_account_execution_by_task(self):
        self.client.force_authenticate(user=self.client_a)

        response = self.client.get(reverse("kpi-execution-by-task", kwargs={"task_id": self.exec_b.celery_task_id}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_generate_sets_execution_owner(self):
        self.client.force_authenticate(user=self.client_a)

        async_result = Mock(id="queued-task-1")
        with patch("agentKPIS.views.generate_and_execute_kpi_task.apply_async", return_value=async_result):
            response = self.client.post(
                reverse("kpi-generate"),
                {"campaign_id": "cmp-a", "campaign_name": "Campaign A"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        created = KPIExecution.objects.get(id=response.data["execution_id"])
        self.assertEqual(created.client_id, self.client_a.id)
