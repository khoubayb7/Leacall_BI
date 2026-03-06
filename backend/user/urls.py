from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("api/login/", views.LoginView.as_view(), name="api_login"),
    path("api/logout/", views.LogoutView.as_view(), name="api_logout"),
    path("api/me/", views.MeView.as_view(), name="api_me"),

    path("api/admin/clients/", views.ClientListCreateView.as_view(), name="admin_clients"),
    path("api/admin/clients/<int:pk>/", views.ClientDetailView.as_view(), name="admin_client_detail"),

    path("api/client/platform/", views.ClientPlatformView.as_view(), name="client_platform"),
]
