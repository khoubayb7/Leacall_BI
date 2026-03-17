from django.urls import path

from . import views

app_name = "etl"

urlpatterns = [
    # Data sources (campaigns)
    path("sources/", views.DataSourceListCreateView.as_view(), name="data_sources"),
    path("sources/<int:pk>/", views.DataSourceDetailView.as_view(), name="data_source_detail"),
    path("sources/<int:data_source_id>/records/", views.CampaignRecordListView.as_view(), name="campaign_records"),

    # ETL runs
    path("runs/", views.ETLRunListView.as_view(), name="etl_runs"),
    path("runs/<int:pk>/", views.ETLRunDetailView.as_view(), name="etl_run_detail"),

    # Trigger sync
    path("sync/", views.ETLSyncView.as_view(), name="etl_sync"),
]
