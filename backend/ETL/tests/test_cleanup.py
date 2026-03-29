from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from ETL.models import ClientDataSource, ETLRun
from ETL.tasks import (
    _cleanup_existing_etl_outputs,
    build_loaded_dataset_snapshot,
    run_single_campaign_etl_task,
)
from ETL.views import ETLSyncView
from user.models import CustomUser


class ETLCleanupOutputTests(TestCase):
    def test_cleanup_existing_etl_outputs_removes_all_artifacts_for_campaign(self) -> None:
        with TemporaryDirectory() as tmp:
            base_dir = Path(tmp) / "etl_output"
            datasets_dir = base_dir / "datasets"
            base_dir.mkdir(parents=True, exist_ok=True)
            datasets_dir.mkdir(parents=True, exist_ok=True)

            matching_files = [
                base_dir / "E_24_campaign.py",
                base_dir / "T_24_campaign.py",
                base_dir / "L_24_campaign.py",
                base_dir / "test_E_24_campaign.py",
                datasets_dir / "dataset_24_campaign.json",
                datasets_dir / "dataset_24_campaign_v2.json",
                datasets_dir / "schema_24_campaign.json",
            ]
            unrelated_file = base_dir / "E_99_other.py"

            for file_path in matching_files + [unrelated_file]:
                file_path.write_text("placeholder", encoding="utf-8")

            _cleanup_existing_etl_outputs(base_dir=base_dir, user_id="24", campaign_id="campaign")

            for file_path in matching_files:
                self.assertFalse(file_path.exists(), f"Expected file to be removed: {file_path}")
            self.assertTrue(unrelated_file.exists(), "Cleanup removed unrelated file")


class ETLDatasetSnapshotCleanupTests(TestCase):
    def setUp(self) -> None:
        self.user = CustomUser.objects.create_user(
            username="client_cleanup",
            email="cleanup@example.com",
            password="secret123",
            role=CustomUser.Role.CLIENT,
        )
        self.data_source = ClientDataSource.objects.create(
            client=self.user,
            campaign_id="cmp-123",
            campaign_name="Campaign 123",
            is_active=True,
        )

    @override_settings(WORKSPACE_DIR=Path("test_workspace_placeholder"))
    def test_build_snapshot_removes_stale_snapshot_variants(self) -> None:
        with TemporaryDirectory() as tmp:
            with override_settings(WORKSPACE_DIR=Path(tmp)):
                datasets_dir = Path(tmp) / "etl_output" / "datasets"
                datasets_dir.mkdir(parents=True, exist_ok=True)

                stale_a = datasets_dir / "dataset_{}_cmp-123_old.json".format(self.user.id)
                stale_b = datasets_dir / "dataset_{}_cmp-123_v2.json".format(self.user.id)
                stale_a.write_text("{}", encoding="utf-8")
                stale_b.write_text("{}", encoding="utf-8")

                snapshot_path, _, _ = build_loaded_dataset_snapshot(
                    client_id=self.user.id,
                    campaign_id="cmp-123",
                    campaign_name="Campaign 123",
                )

                current = Path(snapshot_path)
                self.assertTrue(current.exists(), "Latest snapshot was not created")

                remaining = sorted(datasets_dir.glob(f"dataset_{self.user.id}_cmp-123*.json"))
                self.assertEqual([current], remaining)


class ETLCleanupFlowTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.user = CustomUser.objects.create_user(
            username="client_flow",
            email="flow@example.com",
            password="secret123",
            role=CustomUser.Role.CLIENT,
        )
        self.data_source = ClientDataSource.objects.create(
            client=self.user,
            campaign_id="cmp-flow",
            campaign_name="Flow Campaign",
            is_active=True,
        )

    def test_manual_sync_flow_queues_background_task(self) -> None:
        request = self.factory.post("/etl/sync/", {"data_source_id": self.data_source.id}, format="json")
        force_authenticate(request, user=self.user)

        async_result = Mock(id="celery-task-123")
        with patch("ETL.views.run_etl_pipeline.apply_async", return_value=async_result) as mocked_apply_async:
            response = ETLSyncView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["status"], "queued")
        self.assertEqual(response.data["task_id"], "celery-task-123")
        self.assertEqual(response.data["data_source_id"], self.data_source.id)
        self.assertEqual(response.data["campaign_id"], self.data_source.campaign_id)
        self.assertEqual(response.data["client_id"], self.user.id)
        self.assertIn("run_id", response.data)

        run = ETLRun.objects.get(pk=response.data["run_id"])
        self.assertEqual(run.status, ETLRun.Status.PENDING)
        mocked_apply_async.assert_called_once_with(args=[self.data_source.id, run.id])

    def test_manual_sync_returns_useful_error_when_queue_fails(self) -> None:
        request = self.factory.post("/etl/sync/", {"data_source_id": self.data_source.id}, format="json")
        force_authenticate(request, user=self.user)

        with patch("ETL.views.run_etl_pipeline.apply_async", side_effect=RuntimeError("redis unavailable")):
            response = ETLSyncView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["status"], "error")
        self.assertEqual(response.data["detail"], "Unable to queue ETL run.")
        self.assertIn("run_id", response.data)

        run = ETLRun.objects.get(pk=response.data["run_id"])
        self.assertEqual(run.status, ETLRun.Status.FAILED)
        self.assertIn("Failed to enqueue ETL task", run.error_message)

    def test_scheduled_flow_uses_same_refresh_helper(self) -> None:
        with patch(
            "ETL.tasks.refresh_campaign_etl_and_schema",
            return_value={"ok": True, "run_id": 1, "error": "", "has_schema_change": False, "columns": []},
        ) as mocked_refresh:
            result = run_single_campaign_etl_task.run(data_source_id=self.data_source.id)

        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["ok"])
        mocked_refresh.assert_called_once()


class ETLToKPIHandoffTests(TestCase):
    """
    Test suite for the ETL→KPI handoff pattern.

    When ETL completes successfully, automatic KPI generation should be triggered.
    When ETL fails, no KPI should be queued. This test class validates both manual
    (via ETLSyncView) and nightly (via run_single_campaign_etl_task) paths.
    """

    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.user = CustomUser.objects.create_user(
            username="handoff_client",
            email="handoff@example.com",
            password="secret123",
            role=CustomUser.Role.CLIENT,
        )
        self.data_source = ClientDataSource.objects.create(
            client=self.user,
            campaign_id="cmp-handoff",
            campaign_name="Handoff Campaign",
            campaign_type="google_ads",
            is_active=True,
        )

    def test_manual_etl_success_queues_kpi_handoff(self) -> None:
        """
        Verify: Manual ETL sync (via run_etl_pipeline) → SUCCESS triggers KPI queue.

        This validates the first integration point: when a user manually syncs ETL,
        and the pipeline completes successfully, the KPI generation should be
        automatically queued without requiring additional user action.
        """
        # Create a pending ETL run (would normally be created by ETLSyncView)
        run = ETLRun.objects.create(
            data_source=self.data_source,
            client=self.user,
            status=ETLRun.Status.PENDING,
        )

        # Mock the ETL executor to succeed, and the KPI task queue
        mock_kpi_task = Mock(id="kpi-task-manual-success-123")

        with patch("ETL.tasks.ETLPipelineExecutor") as mock_executor_class, \
             patch("ETL.tasks._generate_etl_files_for_source", return_value=(True, "")), \
             patch("ETL.tasks._queue_kpi_after_etl_success") as mock_queue_kpi:

            # Configure the executor mock to return a successful run
            mock_executor = Mock()
            mock_executor.execute.return_value = ETLRun.objects.create(
                data_source=self.data_source,
                client=self.user,
                status=ETLRun.Status.SUCCESS,
                stats={"extract": {"columns": ["id", "name"]}},
            )
            mock_executor_class.return_value = mock_executor

            # Execute the manual ETL task
            from ETL.tasks import run_etl_pipeline
            run_etl_pipeline.run(data_source_id=self.data_source.id, run_id=run.id)

            # Verify KPI handoff was queued (called exactly once, with success)
            mock_queue_kpi.assert_called_once()
            call_args = mock_queue_kpi.call_args
            self.assertEqual(call_args.kwargs["data_source"], self.data_source)
            self.assertEqual(call_args.kwargs["force_regenerate"], False)

    def test_manual_etl_failure_does_not_queue_kpi_handoff(self) -> None:
        """
        Verify: Manual ETL sync (via run_etl_pipeline) → FAILURE skips KPI queue.

        This ensures the handoff is conditional: KPI should only be queued when the
        ETL pipeline actually succeeds. Failed ETLs should not trigger KPI generation.
        """
        # Create a pending ETL run
        run = ETLRun.objects.create(
            data_source=self.data_source,
            client=self.user,
            status=ETLRun.Status.PENDING,
        )

        with patch("ETL.tasks.ETLPipelineExecutor") as mock_executor_class, \
             patch("ETL.tasks._queue_kpi_after_etl_success") as mock_queue_kpi:

            # Configure the executor mock to return a failed run
            mock_executor = Mock()
            mock_executor.execute.return_value = ETLRun.objects.create(
                data_source=self.data_source,
                client=self.user,
                status=ETLRun.Status.FAILED,
                error_message="ETL extraction failed",
            )
            mock_executor_class.return_value = mock_executor

            # Execute the manual ETL task
            from ETL.tasks import run_etl_pipeline
            run_etl_pipeline.run(data_source_id=self.data_source.id, run_id=run.id)

            # Verify KPI handoff was NOT queued (should not be called on failure)
            mock_queue_kpi.assert_not_called()

    def test_nightly_etl_success_queues_kpi_handoff(self) -> None:
        """
        Verify: Nightly ETL task (via run_single_campaign_etl_task) → SUCCESS triggers KPI queue.

        This validates the second integration point: when the nightly Beat schedule
        runs ETL for a campaign, and it succeeds, KPI generation should be queued
        so the morning dashboard shows current KPIs synced with overnight data.
        """
        with patch("ETL.tasks.refresh_campaign_etl_and_schema") as mock_refresh, \
             patch("ETL.tasks._queue_kpi_after_etl_success") as mock_queue_kpi:

            # Configure the refresh mock to return success
            mock_refresh.return_value = {
                "ok": True,
                "run_id": 999,
                "status": ETLRun.Status.SUCCESS,
                "columns": ["id", "name", "revenue"],
                "has_schema_change": False,
                "current_signature": "sig123",
                "previous_signature": "sig123",
                "error": "",
            }

            # Execute the nightly ETL task
            result = run_single_campaign_etl_task.run(data_source_id=self.data_source.id)

            # Verify the task completed successfully
            self.assertEqual(result["status"], "completed")
            self.assertTrue(result["ok"])

            # Verify KPI handoff was queued
            mock_queue_kpi.assert_called_once()
            call_args = mock_queue_kpi.call_args
            self.assertEqual(call_args.kwargs["data_source"], self.data_source)
            self.assertEqual(call_args.kwargs["etl_run_id"], 999)
            self.assertEqual(call_args.kwargs["force_regenerate"], False)

    def test_nightly_etl_failure_does_not_queue_kpi_handoff(self) -> None:
        """
        Verify: Nightly ETL task (via run_single_campaign_etl_task) → FAILURE skips KPI queue.

        This ensures the handoff respects the same success-only constraint for
        nightly tasks: KPI should only be queued when the nightly ETL succeeds.
        """
        with patch("ETL.tasks.refresh_campaign_etl_and_schema") as mock_refresh, \
             patch("ETL.tasks._queue_kpi_after_etl_success") as mock_queue_kpi:

            # Configure the refresh mock to return failure
            mock_refresh.return_value = {
                "ok": False,
                "run_id": 998,
                "status": ETLRun.Status.FAILED,
                "columns": [],
                "has_schema_change": False,
                "current_signature": "",
                "previous_signature": "",
                "error": "Connection timeout",
            }

            # Execute the nightly ETL task
            result = run_single_campaign_etl_task.run(data_source_id=self.data_source.id)

            # Verify the task returned failure status
            self.assertEqual(result["status"], "completed")
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"], "Connection timeout")

            # Verify KPI handoff was NOT queued
            mock_queue_kpi.assert_not_called()
