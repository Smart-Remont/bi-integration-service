class APIV1PrefixConfig:
    prefix: str = "/v1"
    ddu_contractors: str = "/ddu_contractors"


class APIBigIntegrationPrefixConfig:
    prefix: str = "/big_integration"


class APIPrefixConfig:
    prefix: str = "/api"
    v1: APIV1PrefixConfig = APIV1PrefixConfig()
    big_integration: APIBigIntegrationPrefixConfig = APIBigIntegrationPrefixConfig()


api_prefix_config = APIPrefixConfig()
