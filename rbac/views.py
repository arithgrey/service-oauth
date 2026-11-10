from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User, Group
import logging

logger = logging.getLogger(__name__)


def is_admin(user):
    return user.groups.filter(name='admin').exists()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users(request):
    if not is_admin(request.user):
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    users = User.objects.prefetch_related('groups').order_by('-date_joined')
    data = [
        {
            'id': u.id,
            'email': u.email,
            'name': u.first_name,
            'group': u.groups.first().name if u.groups.exists() else None,
        }
        for u in users
    ]
    return Response(data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def assign_group(request, user_id):
    if not is_admin(request.user):
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    group_name = request.data.get('group')
    if group_name not in ('admin', 'ecommerce'):
        return Response({'error': 'group debe ser admin o ecommerce'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    group = Group.objects.get(name=group_name)
    target_user.groups.clear()
    target_user.groups.add(group)

    logger.info(f"Usuario {target_user.email} asignado al grupo '{group_name}' por {request.user.email}")
    return Response({'id': target_user.id, 'email': target_user.email, 'group': group_name}, status=status.HTTP_200_OK)
