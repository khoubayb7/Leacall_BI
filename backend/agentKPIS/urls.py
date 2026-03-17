from django.urls import path

from agentKPIS import views

urlpatterns = [
    path("generate/", views.GenerateKPIAPIView.as_view(), name="kpi-generate"),
    path("campaign-options/", views.CampaignOptionsAPIView.as_view(), name="kpi-campaign-options"),
    path("executions/", views.KPIExecutionListAPIView.as_view(), name="kpi-execution-list"),
    path("executions/<int:execution_id>/", views.KPIExecutionDetailAPIView.as_view(), name="kpi-execution-detail"),
    path("executions/by-task/<str:task_id>/", views.KPIExecutionByTaskAPIView.as_view(), name="kpi-execution-by-task"),
]

