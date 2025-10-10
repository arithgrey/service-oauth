from django.urls import path, include
from rest_framework.routers import DefaultRouter
from login.views import LoginViewSet, LoginSiginViewSet, TokenViewSet, GoogleLoginViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
urlpatterns = [
    path('signup/', LoginViewSet.signup, name='signup'),
    path('sigin/', LoginSiginViewSet.sigin, name='sigin'),    
    path('refresh-token/', TokenViewSet.refresh_token , name='refresh_token'),
    path('google/', GoogleLoginViewSet.google_login, name='google_login'),
]