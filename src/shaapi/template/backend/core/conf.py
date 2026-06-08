from functools import lru_cache
import os
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.core.path_conf import ApiV2Path


class Settings(BaseSettings):
    """Global settings.

    Every field has a sane development default so the app boots out of the box
    (e.g. ``docker-run.sh up`` with the bundled docker-compose). Override via the
    ``.env`` file for your own setup, and ALWAYS set real secrets in production.
    """

    model_config = SettingsConfigDict(
        env_file=f'{ApiV2Path}/.env', env_file_encoding='utf-8', extra='ignore'
    )

    APP_NAME: str = 'shaapi'

    # Env Config
    ENVIRONMENT: Literal['dev', 'preprod', 'prod'] = 'dev'

    # Database schema bootstrap: in dev, tables are auto-created on startup for a
    # zero-friction first run. In production set DB_AUTO_CREATE=false and rely on
    # Alembic migrations (`shaapi makemigrations` / `shaapi migrate`).
    DB_AUTO_CREATE: bool = True

    # Observability (opt-in). When disabled, the OpenTelemetry/Prometheus stack
    # is never imported, keeping the lean core lightweight.
    OBSERVABILITY_ENABLED: bool = False
    OTLP_GRPC_ENDPOINT: str | None = None

    # Postgres
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = 'postgres'
    POSTGRES_PASSWORD: str = 'postgres'
    POSTGRES_ECHO: bool = False
    POSTGRES_DATABASE: str = 'shaapi'

    CLIENT_URL: str = 'http://localhost:3000'

    # Redis
    REDIS_HOST: str = 'localhost'
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_DATABASE: int = 0
    REDIS_TIMEOUT: int = 5

    # Object storage (MinIO / S3-compatible)
    MINIO_ENDPOINT: str = 'localhost:9000'
    MINIO_PORT: int = 9000
    MINIO_ACCESS_KEY: str = 'minioadmin'
    MINIO_SECRET_KEY: str = 'minioadmin'
    MINIO_BUCKET_NAME: str = 'shaapi'
    MINIO_CLOUD_URL: str = 'http://localhost:9000'

    # SMTP / email (optional: leave blank to disable outgoing mail)
    SMTP_TLS: str = 'True'
    SMTP_PORT: str = '587'
    SMTP_HOST: str = ''
    SMTP_USER: str = ''
    EMAILS_FROM_EMAIL: str = ''
    EMAILS_FROM_NAME: str = ''
    SMTP_PASSWORD: str = ''
    EMAIL_TEMPLATES_DIR: str = os.getcwd() + '/templates/build'

    # Token / crypto secrets — CHANGE THESE IN PRODUCTION
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    TOKEN_SECRET_KEY: str = 'dev-insecure-change-me-token-secret-key'
    # Generate with: python -c "import os; print(os.urandom(32).hex())"
    OPERA_LOG_ENCRYPT_SECRET_KEY: str = 'dev-insecure-change-me-opera-log-key'

    # Google SSO (optional)
    GOOGLE_CLIENT_ID: str = ''
    GOOGLE_SECRET_KEY: str = ''
    GOOGLE_WEBHOOK_OAUTH_REDIRECT_URI: str = ''

    # FastAPI
    FASTAPI_API_V1_PATH: str = '/api/v1'
    FASTAPI_TITLE: str = 'shaapi'
    FASTAPI_VERSION: str = '0.0.1'
    FASTAPI_DESCRIPTION: str = 'A lean, batteries-included FastAPI backend.'
    FASTAPI_DOCS_URL: str | None = f'{FASTAPI_API_V1_PATH}/docs'
    FASTAPI_REDOCS_URL: str | None = f'{FASTAPI_API_V1_PATH}/redocs'
    FASTAPI_OPENAPI_URL: str | None = f'{FASTAPI_API_V1_PATH}/openapi'
    FASTAPI_STATIC_FILES: bool = False

    # Token
    TOKEN_ALGORITHM: str = 'HS256'
    TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24 * 1  # access token lifetime
    TOKEN_REFRESH_EXPIRE_SECONDS: int = 60 * 60 * 24 * 7  # refresh token lifetime
    TOKEN_REDIS_PREFIX: str = 'shaapi:token'
    USER_SECURE_TOKEN_REDIS_PREFIX: str = 'shaapi:user:token'
    ADMIN_SECURE_TOKEN_REDIS_PREFIX: str = 'shaapi:admin:token'
    TOKEN_REFRESH_REDIS_PREFIX: str = 'shaapi:refresh_token'
    CAPTCHA_LOGIN_REDIS_PREFIX: str = 'shaapi:captcha:login'
    TOKEN_REQUEST_PATH_EXCLUDE: list[str] = [  # JWT / RBAC whitelist
        f'/admin{FASTAPI_API_V1_PATH}/auth/login',
        f'/admin{FASTAPI_API_V1_PATH}/auth/token/new',
    ]

    # JWT
    JWT_USER_REDIS_PREFIX: str = 'shaapi:user'
    JWT_ADMIN_REDIS_PREFIX: str = 'shaapi:admin'
    JWT_USER_REDIS_EXPIRE_SECONDS: int = 60 * 60 * 24 * 7

    # Permission (RBAC)
    PERMISSION_MODE: Literal['casbin', 'role-menu'] = 'casbin'
    PERMISSION_REDIS_PREFIX: str = 'shaapi:permission'

    # Casbin RBAC whitelist
    RBAC_CASBIN_EXCLUDE: set[tuple[str, str]] = {
        ('POST', f'/admin{FASTAPI_API_V1_PATH}/auth/logout'),
        ('POST', f'/admin{FASTAPI_API_V1_PATH}/auth/token/new'),
    }

    # Role-Menu
    RBAC_ROLE_MENU_EXCLUDE: list[str] = [
        'sys:monitor:redis',
        'sys:monitor:server',
    ]

    # Cookies
    COOKIE_REFRESH_TOKEN_KEY: str = 'shaapi_refresh_token'
    COOKIE_REFRESH_TOKEN_EXPIRE_SECONDS: int = TOKEN_REFRESH_EXPIRE_SECONDS

    # Log
    LOG_ROOT_LEVEL: str = 'NOTSET'
    LOG_STD_FORMAT: str = (
        '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</> | <lvl>{level: <8}</> | '
        '<cyan> {correlation_id} </> | <lvl>{message}</>'
    )
    LOG_LOGURU_FORMAT: str = (
        '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</> | <lvl>{level: <8}</> | '
        '<cyan> {correlation_id} </> | <lvl>{message}</>'
    )
    LOG_CID_DEFAULT_VALUE: str = '-'
    LOG_CID_UUID_LENGTH: int = 32  # must <= 32
    LOG_STDOUT_LEVEL: str = 'INFO'
    LOG_STDERR_LEVEL: str = 'ERROR'
    LOG_STDOUT_FILENAME: str = 'shaapi_access.log'
    LOG_STDERR_FILENAME: str = 'shaapi_error.log'

    # Middleware
    MIDDLEWARE_CORS: bool = True
    MIDDLEWARE_ACCESS: bool = True

    # Trace ID
    TRACE_ID_REQUEST_HEADER_KEY: str = 'X-Request-ID'

    # CORS
    CORS_ALLOWED_ORIGINS: list[str] = [
        'http://localhost:3000',  # Front-end address, no trailing '/'
    ]
    CORS_EXPOSE_HEADERS: list[str] = [
        TRACE_ID_REQUEST_HEADER_KEY,
    ]

    # DateTime
    DATETIME_TIMEZONE: str = 'Africa/Abidjan'
    DATETIME_FORMAT: str = '%Y-%m-%d %H:%M:%S'

    # Request limiter
    REQUEST_LIMITER_REDIS_PREFIX: str = 'shaapi:limiter'

    # Demo mode (only GET, OPTIONS requests are allowed)
    DEMO_MODE: bool = False
    DEMO_MODE_EXCLUDE: set[tuple[str, str]] = {
        ('POST', f'{FASTAPI_API_V1_PATH}/auth/login'),
        ('POST', f'{FASTAPI_API_V1_PATH}/auth/logout'),
        ('GET', f'{FASTAPI_API_V1_PATH}/auth/captcha'),
    }

    # IP location
    IP_LOCATION_PARSE: Literal['online', 'offline', 'false'] = 'online'
    IP_LOCATION_REDIS_PREFIX: str = 'shaapi:ip:location'
    IP_LOCATION_EXPIRE_SECONDS: int = 60 * 60 * 24 * 1

    # Opera log
    OPERA_LOG_PATH_EXCLUDE: list[str] = [
        '/favicon.ico',
        FASTAPI_DOCS_URL,
        FASTAPI_REDOCS_URL,
        FASTAPI_OPENAPI_URL,
        f'{FASTAPI_API_V1_PATH}/auth/login/swagger',
    ]
    OPERA_LOG_ENCRYPT_TYPE: int = 1  # 0: AES; 1: md5; 2: ItsDangerous; 3: plain; other: ******
    OPERA_LOG_ENCRYPT_KEY_INCLUDE: list[str] = [  # values to encrypt in request bodies
        'password',
        'old_password',
        'new_password',
        'confirm_password',
    ]


@lru_cache
def get_settings() -> Settings:
    """Return the cached global settings instance."""
    return Settings()


# Configuration instance
settings = get_settings()
