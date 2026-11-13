import hashlib

from django.test import TestCase
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from store.models import PagePermission
from store.signals import run_seed


class SeedAdminTest(TestCase):
    """El seed debe dejar al admin usable de raíz: creado, con flags de admin,
    password compatible con el hash SHA-256 que manda el frontend, en el grupo
    admin y con el permiso 'ingresos'. Idempotente."""

    EMAIL = "seedadmin@test.com"
    PLAINTEXT = "seedadmin@test.com"

    def _sha256(self, value):
        return hashlib.sha256(value.encode()).hexdigest()

    def test_seed_creates_admin_user_with_admin_flags(self):
        run_seed(admin_email=self.EMAIL, admin_password=self.PLAINTEXT)

        user = User.objects.get(email=self.EMAIL)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_seed_sets_password_matching_frontend_sha256_hash(self):
        run_seed(admin_email=self.EMAIL, admin_password=self.PLAINTEXT)

        # el frontend envía el password ya hasheado en SHA-256
        authenticated = authenticate(
            username=self.EMAIL, password=self._sha256(self.PLAINTEXT)
        )
        self.assertIsNotNone(authenticated)

    def test_seed_assigns_admin_group_and_ingresos_permission(self):
        run_seed(admin_email=self.EMAIL, admin_password=self.PLAINTEXT)

        user = User.objects.get(email=self.EMAIL)
        self.assertTrue(user.groups.filter(name="admin").exists())
        self.assertTrue(
            PagePermission.objects.filter(
                group__name="admin", page_slug="ingresos"
            ).exists()
        )

    def test_seed_is_idempotent(self):
        run_seed(admin_email=self.EMAIL, admin_password=self.PLAINTEXT)
        run_seed(admin_email=self.EMAIL, admin_password=self.PLAINTEXT)

        self.assertEqual(User.objects.filter(email=self.EMAIL).count(), 1)
