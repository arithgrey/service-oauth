from django.urls import path
from rbac import views

urlpatterns = [
    path('users/', views.list_users),
    path('users/<int:user_id>/group/', views.assign_group),
]
