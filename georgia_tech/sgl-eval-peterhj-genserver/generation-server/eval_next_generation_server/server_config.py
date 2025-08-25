from typing import Any, Optional
from dataclasses import dataclass
import asyncio
import json
import hmac

from fastapi import HTTPException

class Keychain:
    def __init__(self):
        with open("keychain.json", "r") as file:
            self._keys_dict = json.loads(file.read())

    def __getitem__(self, name: str) -> str:
        return self._keys_dict[name]

@dataclass
class ServerConfig:
    default_key: Optional[str] = "dev"
    journal_path: Optional[str] = None

    _keychain: Any = None
    _journal_lock: Any = None

    def __post_init__(self):
        if self.default_key is not None:
            self._keychain = Keychain()
        if self.journal_path is not None:
            self._journal_lock = asyncio.Lock()

    def authorize_request(self, authorization, request):
        if self.default_key is None:
            return
        if authorization is None:
            raise HTTPException(status_code=401)
        api_key = self._keychain[self.default_key]
        if not hmac.compare_digest(authorization, f"Bearer {api_key}"):
            raise HTTPException(status_code=401)

    def authorize_anthropic_request(self, authorization, request):
        if self.default_key is None:
            return
        if authorization is None:
            raise HTTPException(status_code=401)
        api_key = self._keychain[self.default_key]
        if not hmac.compare_digest(authorization, api_key):
            raise HTTPException(status_code=401)
