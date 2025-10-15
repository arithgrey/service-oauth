from django.urls import path, include
from rest_framework.routers import DefaultRouter
from user.views import UserValidatorViewSet, UserSearchViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()

urlpatterns = [
    path('exists/<str:email>', UserValidatorViewSet.as_view({'get': 'user_exists'}), name='exists'),
    path('user-search/', UserSearchViewSet.search_users, name='user_search'),
    path('', include(router.urls)),
]
