"""
Service layer — leacall_bi → leacall REST API.

Toutes les communications avec le serveur leacall d'un client
passent par ce module. Les views appellent ce service,
jamais l'API leacall directement.
"""
import requests
from rest_framework import status


class LeacallAPIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code or 500


class LeacallClient:
    """
    Client HTTP pour un serveur leacall spécifique.
    Instancié à partir des credentials stockés sur le CustomUser.
    """

    def __init__(self, user):
        if not user.leacall_tenancy_url:
            raise LeacallAPIError("Ce client n'a pas de serveur leacall configuré.")

        self.base_url = user.leacall_tenancy_url.rstrip('/')
        self.headers  = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if user.leacall_api_key:
            self.headers['Authorization'] = f'Bearer {user.leacall_api_key}'

    def _request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.request(
                method,
                url,
                headers=self.headers,
                timeout=30,
                **kwargs,
            )
        except requests.exceptions.ConnectionError:
            raise LeacallAPIError(f"Impossible de joindre le serveur leacall : {self.base_url}")
        except requests.exceptions.Timeout:
            raise LeacallAPIError("Le serveur leacall n'a pas répondu dans les délais.")

        if response.status_code == 401:
            raise LeacallAPIError("Credentials leacall invalides.", status_code=401)
        if not response.ok:
            raise LeacallAPIError(
                f"Erreur leacall {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        return response.json()

    # ── Méthodes publiques ────────────────────────────────────────────────

    def get(self, endpoint, params=None):
        return self._request('GET', endpoint, params=params)

    def post(self, endpoint, data=None):
        return self._request('POST', endpoint, json=data)