import os
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
]

@receiver(post_migrate)
def create_stors(sender, **kargs):
    if config('DJANGO_RUNNING_MIGRATIONS',default=False, cast=bool):
        if sender.name == "store":
            data = [
                {"id":1, "name":"Enid Service"},
                {"id":2, "name":"RIMO"},
                {"id":3, "name":"Carpas reforzadas"},
                ]

            for item in data:
                Store.objects.get_or_create(**item)

            admin_group, _ = Group.objects.get_or_create(name='admin')
            Group.objects.get_or_create(name='ecommerce')

            for slug in ADMIN_SLUGS:
                PagePermission.objects.get_or_create(group=admin_group, page_slug=slug)

            admin_email = config('ADMIN_SEED_EMAIL', default='enidservice@gmail.com')
            try:
                admin_user = User.objects.get(email=admin_email)
                admin_user.groups.clear()
                admin_user.groups.add(admin_group)
            except User.DoesNotExist:
                pass