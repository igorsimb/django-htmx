from django.urls import path
from films import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("register/", views.RegisterView.as_view(), name="register"),
]

htmx_views = [
    path('check_username/', views.check_username, name='check_username')
]

urlpatterns += htmx_views