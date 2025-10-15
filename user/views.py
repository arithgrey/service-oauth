from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from django.contrib.auth.models import User
from django.db.models import Q
from user.serializers.user_serializers import UserSerializer
import logging

logger = logging.getLogger(__name__)

class UserValidatorViewSet(viewsets.ViewSet):
    
    @action(detail=False, methods=['GET'], url_path='exists')
    def user_exists(self, request, email=None):
        exists =False
        if email is None:
            return Response({'error':"email is required!"}, status=status.HTTP_400_BAD_REQUEST)    
        
        try:
            User.objects.get(email=email)            
            exists = True
        
        except User.DoesNotExist:
            exists =False            

        return Response({"exists":exists}, status=status.HTTP_200_OK)


class UserSearchViewSet(viewsets.ViewSet):
    """
    ViewSet para búsqueda y listado de usuarios
    """
    
    @api_view(['GET'])
    def search_users(request):
        """
        Endpoint para búsqueda de usuarios
        
        Query Parameters:
        - q: Término de búsqueda (email, username, first_name, last_name)
        - is_active: Filtro por estado (all, true, false)
        
        Response:
        [
            {
                "id": 1,
                "username": "usuario",
                "email": "usuario@email.com",
                "first_name": "Nombre",
                "last_name": "Apellido",
                "is_active": true,
                "is_staff": false,
                "is_superuser": false,
                "date_joined": "2025-01-01T00:00:00Z",
                "last_login": "2025-01-10T00:00:00Z",
                "groups": ["ecommerce"]
            }
        ]
        """
        try:
            # Obtener parámetros de búsqueda
            search_query = request.GET.get('q', '').strip()
            is_active_filter = request.GET.get('is_active', 'all').strip()
            
            # Construir query base
            users = User.objects.all()
            
            # Aplicar filtro de búsqueda
            if search_query:
                users = users.filter(
                    Q(email__icontains=search_query) |
                    Q(username__icontains=search_query) |
                    Q(first_name__icontains=search_query) |
                    Q(last_name__icontains=search_query)
                )
            
            # Aplicar filtro de estado activo
            if is_active_filter == 'true':
                users = users.filter(is_active=True)
            elif is_active_filter == 'false':
                users = users.filter(is_active=False)
            # Si es 'all', no filtramos
            
            # Ordenar por fecha de creación (más recientes primero)
            users = users.order_by('-date_joined')
            
            # Serializar datos
            serialized_users = []
            for user in users:
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'date_joined': user.date_joined,
                    'last_login': user.last_login,
                    'groups': [group.name for group in user.groups.all()]
                }
                serialized_users.append(user_data)
            
            logger.info(f"Búsqueda de usuarios: query='{search_query}', is_active='{is_active_filter}', resultados={len(serialized_users)}")
            
            return Response(serialized_users, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error en búsqueda de usuarios: {str(e)}")
            return Response(
                {'error': 'Error al buscar usuarios'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


