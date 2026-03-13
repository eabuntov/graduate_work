import httpx
from abc import ABC
from urllib.parse import urlencode
from config.settings import settings


def build_oauth_providers() -> list["OAuthProvider"]:
    providers = []
    for name, config in settings.OAUTH_PROVIDERS.items():
        providers.append(OAuthProvider(name, config))
    return providers



class OAuthProvider(ABC):
    providers: dict[str, "OAuthProvider"] = {}

    def __init__(self, name: str, config: dict):
        self.name = name
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.authorize_url = config["authorize_url"]
        self.access_token_url = config["access_token_url"]
        self.userinfo_url = config["userinfo_url"]
        self.scope = config.get("scope", "")

    # ---------- Authorization ----------

    def get_authorize_url(self, redirect_uri: str, state: str | None = None) -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": self.scope,
        }
        if state:
            params["state"] = state

        return f"{self.authorize_url}?{urlencode(params)}"

    # ---------- Token exchange ----------

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                self.access_token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        resp.raise_for_status()
        return resp.json()

    # ---------- User info ----------

    async def fetch_userinfo(self, access_token: str) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )

        resp.raise_for_status()
        return resp.json()

    # ---------- Registry ----------

    @classmethod
    def get_provider(cls, name: str) -> "OAuthProvider":
        if not cls.providers:
            cls._register_providers()
        return cls.providers[name]

    @classmethod
    def _register_providers(cls):
        for provider in build_oauth_providers():
            cls.providers[provider.name] = provider
