"""
Service layer — leacall_bi → leacall REST API.

Toutes les communications avec le serveur leacall d'un client
passent par ce module. Les views appellent ce service,
jamais l'API leacall directement.
"""
import requests
from django.conf import settings
from urllib.parse import parse_qs, urlparse
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


# ── BI read-only client ───────────────────────────────────────────────────────


class LeacallBIClient:
    """
    Read-only HTTP client for the LeaCall BI REST API.
    Authenticates via X-BI-API-Key header.
    """

    def __init__(self, user):
        if not user.leacall_tenancy_url:
            raise LeacallAPIError("Ce client n'a pas de serveur leacall configuré.")

        bi_key = user.leacall_bi_api_key or user.leacall_api_key or settings.LEACALL_BI_API_KEY
        if not bi_key:
            raise LeacallAPIError("Ce client n'a pas de clé API BI configurée.")

        self.base_url = user.leacall_tenancy_url.rstrip('/')
        self.headers = {
            'Accept': 'application/json',
            'X-BI-API-Key': bi_key,
        }

    def _request(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30,
            )
        except requests.exceptions.ConnectionError:
            raise LeacallAPIError(f"Impossible de joindre le serveur leacall : {self.base_url}")
        except requests.exceptions.Timeout:
            raise LeacallAPIError("Le serveur leacall n'a pas répondu dans les délais.")

        if response.status_code == 403:
            raise LeacallAPIError("Clé API BI invalide ou manquante.", status_code=403)
        if not response.ok:
            raise LeacallAPIError(
                f"Erreur leacall BI {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        return response.json()

    # ── Endpoint helpers ─────────────────────────────────────────────────

    def get_users(self):
        """GET /api/bi/users/"""
        return self._request('/api/bi/users/')

    def get_campaign(self, campaign_id):
        """GET /api/bi/campaigns/<campaign_id>/"""
        return self._request(f'/api/bi/campaigns/{campaign_id}/')

    def get_campaign_leads(self, campaign_id, page=None):
        """GET /api/bi/campaigns/<campaign_id>/leads/?page=N"""
        params = {'page': page} if page else None
        return self._request(f'/api/bi/campaigns/{campaign_id}/leads/', params=params)

    def get_all_campaign_leads(self, campaign_id):
        """Fetch all pages of leads for a campaign, handling BI pagination."""
        leads = []
        page = None
        while True:
            data = self.get_campaign_leads(campaign_id, page=page)
            leads.extend(data.get('results', []))
            next_url = data.get('next')
            if not next_url:
                break
            parsed = urlparse(next_url)
            qs = parse_qs(parsed.query)
            page = qs.get('page', [None])[0]
        return leads

    def get_lead_call_attempts(self, lead_id):
        """GET /api/bi/leads/<lead_id>/call-attempts/"""
        return self._request(f'/api/bi/leads/{lead_id}/call-attempts/')

    # Generic get for extractor compatibility
    def get(self, endpoint, params=None):
        return self._request(endpoint, params=params)