from fastapi import APIRouter

from .ddu_flat_list_by_resident.router import router as ddu_flat_list_by_resident_router
from .ddu_flat_remont_info.router import router as ddu_flat_remont_info_router
from .ddu_resident_list.router import router as ddu_resident_list_router
from .ddu_room_list.router import router as ddu_room_list_router
from .ddu_room_type_list.router import router as ddu_room_type_list_router

router = APIRouter(tags=["DDU Export"])
router.include_router(ddu_flat_list_by_resident_router)
router.include_router(ddu_flat_remont_info_router)
router.include_router(ddu_resident_list_router)
router.include_router(ddu_room_list_router)
router.include_router(ddu_room_type_list_router)
