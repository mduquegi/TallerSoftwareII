import os
import uuid

from locust import HttpUser, between, tag, task


PAGE_SIZE = min(int(os.getenv("LOCUST_PAGE_SIZE", "50")), 200)


class ApiUser(HttpUser):
    abstract = True
    host = os.getenv("LOCUST_HOST", "http://127.0.0.1:8000")
    wait_time = between(1, 3)

    def _check_page(self, response, endpoint):
        if response.status_code != 200:
            response.failure(f"{endpoint}: HTTP {response.status_code}")
            return

        try:
            body = response.json()
        except ValueError:
            response.failure(f"{endpoint}: la respuesta no es JSON")
            return

        if not isinstance(body.get("data"), list) or "current_page" not in body:
            response.failure(f"{endpoint}: respuesta sin estructura paginada")

    @tag("get", "users")
    @task(5)
    def list_users(self):
        with self.client.get(
            f"/api/users?page=1&per_page={PAGE_SIZE}",
            name="/api/users",
            catch_response=True,
        ) as response:
            self._check_page(response, "/api/users")

    @tag("get", "emails")
    @task(3)
    def list_emails(self):
        with self.client.get(
            f"/api/users/emails?page=1&per_page={PAGE_SIZE}",
            name="/api/users/emails",
            catch_response=True,
        ) as response:
            self._check_page(response, "/api/users/emails")

    @tag("get", "over-twenty")
    @task(2)
    def list_adults(self):
        with self.client.get(
            f"/api/users/over-twenty?page=1&per_page={PAGE_SIZE}",
            name="/api/users/over-twenty",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"/api/users/over-twenty: HTTP {response.status_code}")
                return

            try:
                body = response.json()
            except ValueError:
                response.failure("/api/users/over-twenty: la respuesta no es JSON")
                return

            users = body.get("users", {})
            if "cutoff_date" not in body or not isinstance(users.get("data"), list):
                response.failure("/api/users/over-twenty: respuesta incompleta")

    @tag("write", "bulk")
    @task(1)
    def create_users(self):
        suffix = uuid.uuid4().hex
        payload = {
            "users": [
                {
                    "name": f"Locust Ana {suffix}",
                    "email": f"ana-{suffix}@loadtest.local",
                    "birth_date": "1998-05-12",
                },
                {
                    "name": f"Locust Bruno {suffix}",
                    "email": f"bruno-{suffix}@loadtest.local",
                    "birth_date": "2000-11-03",
                    "password": "secreto123",
                },
                {
                    "name": f"Locust Carla {suffix}",
                    "email": f"carla-{suffix}@loadtest.local",
                    "birth_date": "1995-01-20",
                },
            ]
        }

        with self.client.post(
            "/api/users/bulk",
            json=payload,
            name="/api/users/bulk",
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                response.failure(f"/api/users/bulk: HTTP {response.status_code}")
                return

            try:
                body = response.json()
            except ValueError:
                response.failure("/api/users/bulk: la respuesta no es JSON")
                return

            if len(body.get("users", [])) != 3:
                response.failure("/api/users/bulk: no se crearon 3 usuarios")


class LoadUser(ApiUser):
    """Carga nominal: usuarios tranquilos y pausas cortas entre solicitudes."""

    weight = 3
    wait_time = between(1, 3)


class StressUser(ApiUser):
    """Estrés: genera más solicitudes por usuario para encontrar el quiebre."""

    weight = 1
    wait_time = between(0.2, 0.8)


class CapacityUser(ApiUser):
    """Capacidad: mantiene una carga constante durante una ejecución larga."""

    weight = 1
    wait_time = between(1, 2)
