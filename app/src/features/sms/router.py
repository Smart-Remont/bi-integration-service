from fastapi import APIRouter

from .call_processing.router import router as call_processing_router
from .sms_notify.router import router as sms_notify_router
from .sms_notify_status.router import router as sms_notify_status_router
from .sms_queue.router import router as sms_queue_router

router = APIRouter(tags=["SMS / Kcell"])

router.include_router(sms_queue_router)
router.include_router(sms_notify_router)
router.include_router(sms_notify_status_router)
router.include_router(call_processing_router)
