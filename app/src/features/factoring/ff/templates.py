from dataclasses import dataclass

import httpx
from fastapi import HTTPException, status
from loguru import logger

TEMPLATE_CODES = {
    "application": "FF_FACTORING_APPLICATION",
    "notification": "FF_FACTORING_NOTIFICATION",
}

PRINT_FORM_SPECS = (
    {
        "name": "application",
        "title": "Заявление о присоединении",
        "file_name": "factoring_application.pdf",
        "template_code": TEMPLATE_CODES["application"],
    },
    {
        "name": "notification",
        "title": "Уведомление о переходе прав",
        "file_name": "factoring_notification.pdf",
        "template_code": TEMPLATE_CODES["notification"],
    },
)


@dataclass(slots=True, frozen=True)
class DocTemplate:
    code: str
    name: str
    path: str


async def fetch_template_bytes(path: str, office_public_url: str) -> bytes:
    relative = path if path.startswith("/") else f"/{path}"
    bases = [
        office_public_url.rstrip("/"),
        "https://office.smartremont.kz",
        "https://devprod.smart-remont.kz",
        "https://devoffice.smart-remont.kz",
    ]
    seen: set[str] = set()
    last_error = "template file was not found"
    timeout = httpx.Timeout(timeout=20.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        for base in bases:
            if not base or base in seen:
                continue
            seen.add(base)
            url = f"{base}{relative}"
            try:
                response = await client.get(url)
            except httpx.RequestError as exc:
                last_error = str(exc)
                logger.warning(
                    "Factoring template fetch failed | url={url} error={error}",
                    url=url,
                    error=exc,
                )
                continue
            if response.status_code == 200 and response.content:
                return response.content
            last_error = f"HTTP {response.status_code} for {url}"
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Не удалось скачать шаблон {relative}: {last_error}",
    )
