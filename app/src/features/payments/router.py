from fastapi import APIRouter

from .forte_pay.router import router as forte_pay_router
from .paybox_pay.router import router as paybox_pay_router
from .sberbank_callback.router import router as sberbank_callback_router
from .sberbank_check_status.router import router as sberbank_check_status_router
from .sberbank_pay.router import router as sberbank_pay_router

router = APIRouter(tags=["Payments"])

router.include_router(sberbank_callback_router)
router.include_router(sberbank_check_status_router)
router.include_router(sberbank_pay_router)
router.include_router(forte_pay_router)
router.include_router(paybox_pay_router)
