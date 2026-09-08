"""Sub-routers from ``IntegrationController.php`` (hs_bi + ``response_json()``).

PHP URL: ``/integration/{action}`` — здесь ``/api/integration/{action}``.
"""

from fastapi import APIRouter

from .big_crm_form.router import router as big_crm_form_router
from .bigapp_form.router import router as bigapp_form_router
from .change_request_status.router import router as change_request_status_router
from .crm_legacy.router import router as crm_legacy_router
from .get_constructives.router import router as get_constructives_router
from .remont_avail.router import router as remont_avail_router
from .showroom_info_list.router import router as showroom_info_list_router
from .sr_preset_list.router import router as sr_preset_list_router
from .sr_remont_avail.router import router as sr_remont_avail_router
from .sr_render.router import router as sr_render_router
from .sr_render_avail.router import router as sr_render_avail_router
from .sr_request_list.router import router as sr_request_list_router
from .sr_resident_report.router import router as sr_resident_report_router
from .sr_showroom_report.router import router as sr_showroom_report_router
from .sr_stage.router import router as sr_stage_router

router = APIRouter(tags=["IntegrationController (hs_bi)"])

router.include_router(sr_render_router)
router.include_router(sr_request_list_router)
router.include_router(sr_preset_list_router)
router.include_router(sr_render_avail_router)
router.include_router(sr_stage_router)
router.include_router(sr_showroom_report_router)
router.include_router(sr_resident_report_router)
router.include_router(sr_remont_avail_router)
router.include_router(remont_avail_router)
router.include_router(get_constructives_router)
router.include_router(change_request_status_router)
router.include_router(bigapp_form_router)
router.include_router(big_crm_form_router)
router.include_router(showroom_info_list_router)
router.include_router(crm_legacy_router)
