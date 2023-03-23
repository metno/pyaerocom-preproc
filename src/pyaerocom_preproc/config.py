from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

if sys.version_info >= (3, 11):  # pragma: no cover
    from importlib import resources
else:  # pragma: no cover
    import importlib_resources as resources

import tomli_w
from dynaconf import Dynaconf, ValidationError, Validator
from loguru import logger

__all__ = ["config"]

SECRETS_PATH = Path(f"~/.config/{__package__}/config.toml").expanduser()


@lru_cache
def _settings(*, secrets: Path = SECRETS_PATH) -> Dynaconf:
    with resources.as_file(resources.files(__package__) / "settings.toml") as settings:
        return Dynaconf(
            envvar_prefix="PYA_PP",
            settings_file=secrets,
            includes=[settings],
            validators=[
                Validator(
                    "s3_bucket.endpoint_url",
                    "s3_bucket.bucket_name",
                    "s3_bucket.access_key_id",
                    "s3_bucket.secret_access_key",
                    must_exist=True,
                )
            ],
        )


@lru_cache
def config(
    *,
    secrets: Path = SECRETS_PATH,
    overwrite: bool = False,
) -> Dynaconf | None:
    """Check S3 credentials file"""
    if not secrets.exists() or overwrite:
        _secrets = {
            key: input(f"{key}: ") for key in ("bucket_name", "access_key_id", "secret_access_key")
        }
        secrets.parent.mkdir(True, exist_ok=True)
        secrets.parent.chmod(0o700)  # only user has read/write/execute permissions
        if _secrets["bucket_name"].startswith("s3://"):
            _secrets["bucket_name"] = _secrets["bucket_name"].replace("s3://", "")
        secrets.write_text(tomli_w.dumps({"s3_bucket": _secrets}))
        secrets.chmod(0o600)  # only user has read/write permissions

    settings = _settings(secrets=secrets)
    try:
        settings.validators.validate("s3_bucket")
    except ValidationError as e:  # pragma: no cover
        logger.bind(path=secrets).error(e)
        return None
    else:
        return settings
