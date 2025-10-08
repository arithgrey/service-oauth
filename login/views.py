from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from login.serializers import UserSignupSerializer, UserSingInValidatorSerializer, GoogleOAuthSerializer
from rest_framework.exceptions import ValidationError
from user.serializers.user_validator_serializers import UserValidatorSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group, User
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests
import logging

logger = logging.getLogger(__name__)


class LoginViewSet(viewsets.ViewSet):
    @api_view(['POST'])
    def signup(request):
        data = request.data
        try:

            errors = LoginViewSet.validator_handler(data=data)
            if errors:
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)    

            serializer = UserSignupSerializer(data=data)
            if serializer.is_valid():
                user = serializer.save()
                perfil = Group.objects.get(name='ecommerce')
                user.groups.add(perfil)

                return  Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except ValidationError as error:
            
            return Response({"detail": error.detail}, status=status.HTTP_400_BAD_REQUEST)


    @staticmethod
    def validator_handler(data):
        errors = {}
        user_serializer = UserValidatorSerializer(data=data)
        if not user_serializer.is_valid():
            errors.update(user_serializer.errors)

        return errors


class LoginSiginViewSet(viewsets.ViewSet):
    
    @api_view(['POST'])
    def sigin(request):        
        data = request.data

        serializer = UserSingInValidatorSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            
            access_token = AccessToken.for_user(user)       
            refresh_token = RefreshToken.for_user(user)                
            profile = user.groups.first().name if user.groups.exists() else None
            user_data = {
               'profile':profile,
               'name': user.first_name,
               'email':user.email,               
            }
            return Response(
                {   'user':user_data,
                    'token': str(access_token), 
                    'refresh_token': str(refresh_token),
                    'profile':profile}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Credenciales inválidas'}, status=status.HTTP_401_UNAUTHORIZED)



class TokenViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @api_view(['POST'])
    def refresh_token(request):       
        try:
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response({'error': 'Refresh token is required'}, status=400)

            token = RefreshToken(refresh_token)
            new_access_token = str(token.access_token)
            new_refresh_token = str(token)
                        
            return Response({'access_token': new_access_token, 'refresh_token': new_refresh_token}, status=200)

        except Exception as e:
            return Response({'error': str(e)}, status=500)


class GoogleLoginViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar autenticación con Google OAuth
    """
    
    @api_view(['POST'])
    def google_login(request):
        """
        Endpoint para autenticación/registro con Google OAuth
        
        Request Body:
        {
            "email": "usuario@gmail.com",
            "name": "Nombre Usuario",
            "google_id": "102938475639201847563",
            "credential": "eyJhbGciOiJSUzI1NiIsImtpZCI6...",
            "picture": "https://lh3.googleusercontent.com/...",
            "email_verified": true
        }
        
        Response:
        {
            "token": "jwt-access-token",
            "refresh_token": "jwt-refresh-token",
            "user": {
                "id": 1,
                "email": "usuario@gmail.com",
                "name": "Nombre Usuario",
                "profile": "ecommerce"
            }
        }
        """
        try:
            # 1. Validar datos del request
            serializer = GoogleOAuthSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"Validación fallida de Google OAuth: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            credential = validated_data['credential']
            email = validated_data['email']
            google_id = validated_data['google_id']
            name = validated_data['name']
            picture = validated_data.get('picture', '')
            
            # 2. Verificar que Google Client ID esté configurado
            google_client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
            if not google_client_id:
                logger.error("GOOGLE_CLIENT_ID no está configurado en settings")
                return Response(
                    {'error': 'Configuración de Google OAuth no disponible'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 3. Validar el token con Google
            try:
                idinfo = id_token.verify_oauth2_token(
                    credential,
                    requests.Request(),
                    google_client_id
                )
                
                # Verificar que el email del token coincida con el proporcionado
                if idinfo.get('email') != email:
                    logger.warning(f"Email mismatch: token={idinfo.get('email')}, request={email}")
                    return Response(
                        {'error': 'El email no coincide con el token de Google'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Verificar que el sub (google_id) coincida
                if idinfo.get('sub') != google_id:
                    logger.warning(f"Google ID mismatch: token={idinfo.get('sub')}, request={google_id}")
                    return Response(
                        {'error': 'El ID de Google no coincide'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            except ValueError as e:
                logger.error(f"Token de Google inválido: {str(e)}")
                return Response(
                    {'error': 'Token de Google inválido o expirado'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            except Exception as e:
                logger.error(f"Error al validar token de Google: {str(e)}")
                return Response(
                    {'error': 'Error al validar con Google'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 4. Buscar o crear usuario
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': name,
                    'email': email
                }
            )
            
            # 5. Actualizar datos del usuario si ya existía
            if not created:
                user.first_name = name
                user.save()
            
            # 6. Asignar perfil 'ecommerce' al usuario si es nuevo
            if created:
                try:
                    perfil = Group.objects.get(name='ecommerce')
                    user.groups.add(perfil)
                    logger.info(f"Usuario creado con Google OAuth: {email}")
                except Group.DoesNotExist:
                    logger.warning(f"Grupo 'ecommerce' no existe, usuario sin grupo: {email}")
            
            # 7. Generar tokens JWT
            access_token = AccessToken.for_user(user)
            refresh_token = RefreshToken.for_user(user)
            
            # 8. Obtener perfil del usuario
            profile = user.groups.first().name if user.groups.exists() else 'ecommerce'
            
            # 9. Preparar datos de respuesta
            user_data = {
                'id': user.id,
                'email': user.email,
                'name': user.first_name,
                'profile': profile
            }
            
            logger.info(f"Login exitoso con Google OAuth: {email}")
            
            # 10. Retornar respuesta
            return Response({
                'token': str(access_token),
                'refresh_token': str(refresh_token),
                'user': user_data
            }, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error inesperado en Google OAuth: {str(e)}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )