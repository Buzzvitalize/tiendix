import os
import warnings


class BaseConfig:
    """Base configuration with safe defaults."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
    if SECRET_KEY == "dev":
        warnings.warn(
            "Using default SECRET_KEY; set the SECRET_KEY environment variable in production",
            UserWarning,
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    PDF_ARCHIVE_ROOT = os.environ.get("PDF_ARCHIVE_ROOT")
    PUBLIC_DOCS_BASE_URL = os.environ.get("PUBLIC_DOCS_BASE_URL")


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.sqlite'


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///database.sqlite')


def validate_runtime_config(config: dict):
    """Fail fast on insecure runtime configuration."""
    if config.get('APP_ENV') == 'production' and not config.get('SECRET_KEY'):
        raise RuntimeError('SECRET_KEY is required in production')
    if not config.get('TESTING', False) and not config.get('WTF_CSRF_ENABLED', True):
        raise RuntimeError('WTF_CSRF_ENABLED must be True outside test environments')
