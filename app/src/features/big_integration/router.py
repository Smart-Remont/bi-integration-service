from fastapi import APIRouter

from .big_notify_client.router import router as big_notify_client_router
from .ddu_flat_info.router import router as ddu_flat_info_router
from .ddu_flat_info_multiple.router import router as ddu_flat_info_multiple_router
from .ddu_request_info.router import router as ddu_request_info_router
from .ddu_resident_agreement_status.router import (
    router as ddu_resident_agreement_status_router,
)
from .remont_preset.router import router as remont_preset_router
from .remont_preset_list_v2.router import router as remont_preset_list_v2_router
from .repair_pack_prices.router import router as repair_pack_prices_router
from .request_constructives.router import router as request_constructives_router
from .request_create_v3.router import router as request_create_v3_router
from .request_event_v3.router import router as request_event_v3_router
from .request_info.router import router as request_info_router
from .request_status_info.router import router as request_status_info_router

router = APIRouter(tags=["BIG Integration"])
router.include_router(big_notify_client_router)
router.include_router(ddu_flat_info_router)
router.include_router(ddu_flat_info_multiple_router)
router.include_router(ddu_request_info_router)
router.include_router(ddu_resident_agreement_status_router)
router.include_router(remont_preset_router)
router.include_router(remont_preset_list_v2_router)
router.include_router(repair_pack_prices_router)
router.include_router(request_constructives_router)
router.include_router(request_create_v3_router)
router.include_router(request_event_v3_router)
router.include_router(request_info_router)
router.include_router(request_status_info_router)
