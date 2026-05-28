from fastapi import APIRouter

from .request_event_v3.router import router as request_event_v3_router

router = APIRouter(tags=["Big Integration"])
router.include_router(request_event_v3_router)
