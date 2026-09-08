"""Legacy BI/CRM shares the exact same hardcoded Basic Auth credentials as BIG
Integration in the legacy PHP controller (`$AUTH_USER='hs_bi'`, same password on
every action) — same partner, same secret, so we reuse the one auth dependency
instead of duplicating a second config pointing at the same credentials.
"""

from src.features.big_integration.auth import BigIntegrationBasicAuthDep

__all__ = ["BigIntegrationBasicAuthDep"]
