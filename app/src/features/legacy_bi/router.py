"""Aggregates legacy BI/CRM sub-routers.

Ported from ``IntegrationController.php`` (BI group). 4 actions from that
group are **not** ported — their stored functions no longer exist in the
database (or their signature no longer matches the PHP call), so porting them
would ship endpoints that always fail:

- ``crmCreateClientRequestEmptyAction`` — ``rest.bi_create_client_request``
  now requires 3 args (``flat_guid_, preset_id_, client_request_id_``); the
  PHP model still calls it with 1 arg.
- ``crmCreateClientRequestAgreementAction`` — ``rest.bi_create_client_request_agreement``
  does not exist.
- ``createRequestAction`` — ``rest.bi_create_request`` does not exist.
- ``srRemontReportAction`` — ``rest.sr_remont_report`` does not exist.
"""

from fastapi import APIRouter

from .big_crm_form.router import router as big_crm_form_router
from .bigapp_form.router import router as bigapp_form_router
from .change_request_status.router import router as change_request_status_router
from .get_constructives.router import router as get_constructives_router
from .remont_avail.router import router as remont_avail_router
from .sr_preset_list.router import router as sr_preset_list_router
from .sr_remont_avail.router import router as sr_remont_avail_router
from .sr_render.router import router as sr_render_router
from .sr_render_avail.router import router as sr_render_avail_router
from .sr_request_list.router import router as sr_request_list_router
from .sr_resident_report.router import router as sr_resident_report_router
from .sr_showroom_report.router import router as sr_showroom_report_router
from .sr_stage.router import router as sr_stage_router

router = APIRouter(tags=["Legacy BI/CRM"])

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
