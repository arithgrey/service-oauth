import hashlib

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from store.models import Store, PagePermission
from django.contrib.auth.models import Group, User
from decouple import config

ADMIN_SLUGS = [
    'search-orders',
    'search-users',
    'search-leads',
    'add-product',
    'stock',
    'multicalendar',
    'impact',
    'experiencia',
    'user-area',
    'user-permissions',
    'ingresos',
]

STORES = [
    {"id": 1, "name": "Enid Service"},
    {"id": 2, "name": "RIMO"},
    {"id": 3, "name": "Carpas reforzadas"},
]


def run_seed(admin_email=None, admin_password=None):
    """Siembra datos base de forma idempotente: stores, grupos, permisos y el
    usuario admin usable de raíz.

    El frontend envía el password ya hasheado en SHA-256, así que el password
    almacenado debe corresponder a ese hash (no al texto plano) para que
    `authenticate(password=sha256hex)` funcione.
    """
    admin_email = admin_email or config('ADMIN_SEED_EMAIL', default='enidservice@gmail.com')
    admin_password = admin_password or config('ADMIN_SEED_PASSWORD', default=admin_email)

    for item in STORES:
        Store.objects.get_or_create(**item)

    admin_group, _ = Group.objects.get_or_create(name='admin')
    Group.objects.get_or_create(name='ecommerce')

    for slug in ADMIN_SLUGS:
        PagePermission.objects.get_or_create(group=admin_group, page_slug=slug)

    password_hash = hashlib.sha256(admin_password.encode()).hexdigest()

    admin_user, _ = User.objects.get_or_create(
        email=admin_email,
        defaults={'username': admin_email},
    )
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.is_active = True
    admin_user.set_password(password_hash)
    admin_user.save()

    admin_user.groups.clear()
    admin_user.groups.add(admin_group)

    return admin_user


@receiver(post_migrate)
def create_stors(sender, **kargs):
    if config('DJANGO_RUNNING_MIGRATIONS', default=False, cast=bool):
        if sender.name == "store":
            run_seed()
