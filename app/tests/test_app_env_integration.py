import os
import subprocess
import sys

from django.test import SimpleTestCase


class AppEnvIntegrationTest(SimpleTestCase):
    """
    Por qué: dev y prod se distinguen SOLO por APP_ENV (spec urls-dinamicas).
    ALLOWED_HOSTS='*' (aprobado; el servicio solo es alcanzable vía nginx con puertos
    a 127.0.0.1) y DEBUG solo en dev. Sin mocks: HTTP real contra la app y un proceso
    Python real que carga settings con cada valor de APP_ENV.
    """

    def test_host_arbitrario_no_es_rechazado_por_allowed_hosts(self):
        for host in ("82.180.161.54", "dominio-cualquiera.example", "localhost"):
            response = self.client.get("/ruta-inexistente/", HTTP_HOST=host)
            self.assertNotEqual(response.status_code, 400, f"Host={host} rechazado")

    def _load_settings(self, app_env):
        env = {**os.environ, "APP_ENV": app_env, "DJANGO_SETTINGS_MODULE": "app.settings"}
        out = subprocess.run(
            [sys.executable, "-c",
             "from django.conf import settings; print(settings.DEBUG, settings.ALLOWED_HOSTS)"],
            env=env, capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()

    def test_prod_tiene_debug_false_y_hosts_abiertos(self):
        self.assertEqual(self._load_settings("prod"), "False ['*']")

    def test_dev_tiene_debug_true_y_hosts_abiertos(self):
        self.assertEqual(self._load_settings("dev"), "True ['*']")
