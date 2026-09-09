from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


class BigIntegrationAuthConfig:
    username: str = os.getenv("INTEGRATION_HS_BI_USER", "hs_bi")
    password: str = os.getenv("INTEGRATION_HS_BI_PASSWORD", "")


class DduExportAuthConfig:
    """Basic auth for /api/ddu_export/* — separate credentials from BIG Integration."""

    username: str = os.getenv("DDU_EXPORT_AUTH_USER", "ddu_export")
    password: str = os.getenv("DDU_EXPORT_AUTH_PASSWORD", "")


class InstallmentAuthConfig:
    username: str = os.getenv("INSTALLMENT_API_USER", "")
    password: str = os.getenv("INSTALLMENT_API_PASSWORD", "")


class FactoringAuthConfig:
    """Basic auth for /api/v1/factoring/*. Falls back to installment creds if unset."""

    username: str = os.getenv(
        "FACTORING_API_USER",
        os.getenv("INSTALLMENT_API_USER", ""),
    )
    password: str = os.getenv(
        "FACTORING_API_PASSWORD",
        os.getenv("INSTALLMENT_API_PASSWORD", ""),
    )


class StorageAuthConfig:
    """Basic auth for /api/v1/storage/*. Falls back to installment creds if unset."""

    username: str = os.getenv(
        "STORAGE_API_USER",
        os.getenv("INSTALLMENT_API_USER", ""),
    )
    password: str = os.getenv(
        "STORAGE_API_PASSWORD",
        os.getenv("INSTALLMENT_API_PASSWORD", ""),
    )


class FactoringPrescoringConfig:
    """HTTP Basic for bank prescoring_factoring (separate from JWT apply-lead)."""

    username: str = os.getenv("FACTORING_PRESCORING_USER", "")
    password: str = os.getenv("FACTORING_PRESCORING_PASSWORD", "")


class CORSConfig:
    allow_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    allow_credentials: bool = True
    allow_methods: List[str] = ["*"]
    allow_headers: List[str] = ["*"]


class MyncaConfig:
    """Client ЭЦП via existing MyNCA (same service as constructor ClientSignController)."""

    base_url: str = os.getenv("MYNCA_BASE_URL", "https://nca.smartremont.kz/api")
    token: str = os.getenv("MYNCA_TOKEN", "")
    office_public_url: str = os.getenv(
        "OFFICE_PUBLIC_URL",
        "https://office.smartremont.kz",
    )
    public_base_url: str = os.getenv(
        "PUBLIC_BASE_URL",
        "https://devintegration.smart-remont.kz",
    )
    # Company EDS keys used to sign cession (assignment) documents live encrypted
    # in nca.company_key_store_tab (same DB, managed by the `myspace` admin app —
    # see myspace-backend/nca/). We decrypt them in Postgres via
    # nca.company_key_store__get_decrypted(id, master_key) — same master key as
    # myspace's NCA_MASTER_KEY env var. Which key to use is resolved from
    # client_request_tab.company_id → nca.company_key_store__read_by_company.
    nca_master_key: str = os.getenv("NCA_MASTER_KEY", "")
    # Public sign page (cabinet stores this as document_url after callback).
    sign_page_url: str = os.getenv("MYNCA_SIGN_PAGE_URL", "https://nca.smartremont.kz/sign/")


class AppConfig:
    env: str = os.getenv("APP_ENV", "stage")


class KcellConfig:
    """Kcell Hermes SMS + batch status polling (legacy ``kcell_send_sms`` / ``kcell_check_batch_status``)."""

    hermes_base_url: str = os.getenv("KCELL_HERMES_BASE_URL", "https://api-cpa.kcell.kz/hermes")
    hermes_user: str = os.getenv("KCELL_HERMES_USER", "")
    hermes_password: str = os.getenv("KCELL_HERMES_PASSWORD", "")
    batch_base_url: str = os.getenv("KCELL_BATCH_BASE_URL", "https://msg.kcell.kz/api/v3/batches")
    batch_user: str = os.getenv("KCELL_BATCH_USER", "")
    batch_password: str = os.getenv("KCELL_BATCH_PASSWORD", "")


class SberbankConfig:
    user: str = os.getenv("SBERBANK_USER", "")
    password: str = os.getenv("SBERBANK_PASSWORD", "")
    password_test: str = os.getenv("SBERBANK_PASSWORD_TEST", "")
    test_mode: bool = os.getenv("SBERBANK_TEST_MODE", "").lower() in ("1", "true", "yes")
    base_url_prod: str = "https://securepayments.sberbank.kz/payment/rest"
    base_url_test: str = "https://3dsec.sberbank.kz/payment/rest"


class PaymentsConfig:
    """Public base URL for payment return/redirect links (legacy ``getHttpHost()``)."""

    public_base_url: str = (
        os.getenv("PAYMENTS_PUBLIC_BASE_URL")
        or os.getenv("OFFICE_PUBLIC_URL")
        or "https://office.smartremont.kz"
    ).rstrip("/")
    kaspi_allowed_ips: tuple[str, ...] = tuple(
        ip.strip()
        for ip in os.getenv("KASPI_ALLOWED_IPS", "194.187.247.152").split(",")
        if ip.strip()
    )
    paybox_enabled: bool = os.getenv("PAYBOX_ENABLED", "false").lower() in ("1", "true", "yes")
    forte_url: str = os.getenv("FORTE_URL", "")
    forte_merchant: str = os.getenv("FORTE_MERCHANT", "")
    paybox_merchant: str = os.getenv("PAYBOX_MERCHANT", "")
    paybox_salt: str = os.getenv("PAYBOX_SALT", "")
    paybox_secret_key: str = os.getenv("PAYBOX_SECRET_KEY", "")
    paybox_init_url: str = os.getenv("PAYBOX_INIT_URL", "")
    paybox_status_url: str = os.getenv("PAYBOX_STATUS_URL", "")


class SigningConfig:
    """Aitu / DID signing (legacy IntegrationController signing actions)."""

    public_base_url: str = (
        os.getenv("SIGNING_PUBLIC_BASE_URL")
        or os.getenv("OFFICE_PUBLIC_URL")
        or "https://office.smartremont.kz"
    ).rstrip("/")
    myspace_api_url: str = os.getenv(
        "MYSPACE_API_URL",
        "https://myspace-api.smartremont.kz",
    ).rstrip("/")
    aitu_base_url: str = os.getenv("AITU_BASE_URL", "").rstrip("/")
    aitu_parse_url: str = os.getenv("AITU_PARSE_URL", "").rstrip("/")
    aitu_client_id: str = os.getenv("AITU_CLIENT", "")
    aitu_client_secret: str = os.getenv("AITU_SECRET", "")
    aitu_redirect_url: str = os.getenv("AITU_REDIRECT_URL", "")


class LeadsConfig:
    albato_meta_token: str = os.getenv("ALBATO_META_TOKEN", "")
    tilda_export_dir: str = os.getenv("TILDA_EXPORT_DIR", "")


class BiConfig:
    showroom_info_url: str = os.getenv(
        "BI_SHOWROOM_INFO_URL",
        "https://opera.bi.group/wbs/api/applications/showroomsmartremont/",
    )


class WorkersConfig:
    bi_api_user: str = os.getenv("BI_API_USER", "hs_smart")
    bi_api_password: str = os.getenv("BI_API_PASSWORD", "")
    bi_placements_url: str = os.getenv(
        "BI_PLACEMENTS_URL",
        "https://apigw.bi.group/ooo/hs/bigroup/apicenter/placements",
    )
    bi_residents_url: str = os.getenv(
        "BI_RESIDENTS_URL",
        "https://apigw.bi.group/ooo/hs/Smart/GetObjectsList?KeyTransferDate=20190101000000",
    )
    bi_crm_create_finish_url: str = os.getenv(
        "BI_CRM_CREATE_FINISH_URL",
        "https://apigw.bi.group/ooo/hs/CRM/create_finish",
    )
    planoplan_token: str = os.getenv("PLANOPLAN_TOKEN", "123456")
    planoplan_api_base: str = os.getenv(
        "PLANOPLAN_API_BASE",
        "https://api.planoplan.com/team/v2",
    ).rstrip("/")
    partner_api_url: str = os.getenv(
        "PARTNER_API_URL",
        "https://bpapi.smartremont.kz/partner",
    ).rstrip("/")
    contractor_agreement_pdf_base: str = os.getenv(
        "CONTRACTOR_AGREEMENT_PDF_BASE",
        "https://bpapi.smartremont.kz/partner/contractor_agreement_list/signed",
    ).rstrip("/")
    freedom_legacy_base_url: str = os.getenv("FF_BASE_URL", "https://fastcash-back.trafficwave.kz")
    freedom_legacy_auth_body: str = os.getenv("FF_AUTH", "")


class MinioConfig:
    """MinIO / S3-compatible storage — same keys as smremont `application.ini` → minio.*."""

    endpoint: str = os.getenv("MINIO_ENDPOINT", "").rstrip("/")
    bucket: str = os.getenv("MINIO_BUCKET", "smartremont")
    access_key: str = os.getenv("MINIO_ACCESS_KEY", "")
    secret_key: str = os.getenv("MINIO_SECRET_KEY", "")
    region: str = os.getenv("MINIO_REGION", "us-east-1")

    @property
    def is_configured(self) -> bool:
        return bool(self.endpoint and self.access_key and self.secret_key and self.bucket)


def _first_nonempty_env(*names: str, default: str) -> str:
    for name in names:
        value = (os.getenv(name) or "").strip()
        if value:
            return value.rstrip("/")
    return default.rstrip("/")


class FileStoreConfig:
    """Public URLs for stored files: STORAGE_PUBLIC_URL + `/documents/...`."""

    public_base_url: str = _first_nonempty_env(
        "STORAGE_PUBLIC_URL",
        "OFFICE_PUBLIC_URL",
        default="https://office.smartremont.kz",
    )

    def file_url(self, logical_path: str) -> str:
        return f"{self.public_base_url}{logical_path}"


cors_config = CORSConfig()
big_integration_auth_config = BigIntegrationAuthConfig()
ddu_export_auth_config = DduExportAuthConfig()
installment_auth_config = InstallmentAuthConfig()
factoring_auth_config = FactoringAuthConfig()
storage_auth_config = StorageAuthConfig()
factoring_prescoring_config = FactoringPrescoringConfig()
mynca_config = MyncaConfig()
app_config = AppConfig()
kcell_config = KcellConfig()
sberbank_config = SberbankConfig()
payments_config = PaymentsConfig()
signing_config = SigningConfig()
leads_config = LeadsConfig()
bi_config = BiConfig()
workers_config = WorkersConfig()
minio_config = MinioConfig()
file_store_config = FileStoreConfig()
