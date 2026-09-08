class APIV1PrefixConfig:
    prefix: str = "/v1"
    ddu_contractors: str = "/ddu_contractors"
    installment_ff: str = "/installment/ff"
    factoring_ff: str = "/factoring/ff"
    storage: str = "/storage"


class APIBigIntegrationPrefixConfig:
    prefix: str = "/big_integration"


class APIDduExportPrefixConfig:
    prefix: str = "/ddu_export"


class APIBiPrefixConfig:
    prefix: str = "/integration"


class APISmsPrefixConfig:
    prefix: str = "/sms"


class APIPaymentsPrefixConfig:
    prefix: str = "/payments"


class APISigningPrefixConfig:
    prefix: str = "/signing"


class APILeadsPrefixConfig:
    prefix: str = "/leads"


class APIWorkersPrefixConfig:
    prefix: str = "/workers"


class APIPrefixConfig:
    prefix: str = "/api"
    v1: APIV1PrefixConfig = APIV1PrefixConfig()
    big_integration: APIBigIntegrationPrefixConfig = APIBigIntegrationPrefixConfig()
    ddu_export: APIDduExportPrefixConfig = APIDduExportPrefixConfig()
    bi: APIBiPrefixConfig = APIBiPrefixConfig()
    sms: APISmsPrefixConfig = APISmsPrefixConfig()
    payments: APIPaymentsPrefixConfig = APIPaymentsPrefixConfig()
    signing: APISigningPrefixConfig = APISigningPrefixConfig()
    leads: APILeadsPrefixConfig = APILeadsPrefixConfig()
    workers: APIWorkersPrefixConfig = APIWorkersPrefixConfig()


api_prefix_config = APIPrefixConfig()
