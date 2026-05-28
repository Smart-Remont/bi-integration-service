class GunicornConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    timeout: int = 900
    workers: int = 4
    log_level: str = "info"


gunicorn_config = GunicornConfig()
