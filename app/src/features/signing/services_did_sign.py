from __future__ import annotations

from .repo import SigningRepository


class DidSignService:
    """Resolve Aitu redirect URL by DID state."""

    def __init__(self, repo: SigningRepository) -> None:
        self.repo = repo

    async def did_sign_url(self, state: str) -> str | None:
        return await self.repo.did_url_get(state)
