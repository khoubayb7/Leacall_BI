from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('signin/',   views.SignInView.as_view(),  name='signin'),
    path('signout/',  views.sign_out_view,          name='signout'),

    # REST API endpoints
    path('api/login/',  views.APILoginView.as_view(),  name='api_login'),
    path('api/logout/', views.APILogoutView.as_view(), name='api_logout'),
]
