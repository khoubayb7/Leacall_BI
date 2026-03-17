from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/etl/", include("ETL.urls")),
    path("api/agent/", include("agent.urls")),
    path("api/kpis/", include("agentKPIS.urls")),
    path("", include("user.urls")),
]
