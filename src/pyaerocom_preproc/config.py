import sys
from getpass import getpass
from pathlib import Path

if sys.version_info >= (3, 11):
    from importlib import resources
else:
    import importlib_resources as resources

import tomli_w
from dynaconf import Dynaconf, ValidationError, Validator
from loguru import logger

__all__ = ["settings", "config_checker"]

SECRETS_PATH = Path(f"~/.config/{__package__}/config.toml").expanduser()


def _settings(secrets: Path) -> Dynaconf:
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


settings = _settings(SECRETS_PATH)


def config_checker(
    *,
    secrets: Path = SECRETS_PATH,
    overwrite: bool = False,
) -> bool:
    """Check S3 credentials file"""
    if not secrets.exists() or overwrite:
        _secrets = {
            key: getpass(f"{key}: ")
            for key in ("bucket_name", "access_key_id", "secret_access_key")
        }
        secrets.parent.mkdir(True, exist_ok=True)
        secrets.parent.chmod(0o700)  # only user has read/write/execute permissions
        secrets.write_text(tomli_w.dumps({"s3_bucket": _secrets}))
        secrets.chmod(0o600)  # only user has read/write permissions

    try:
        _settings(secrets).validators.validate("s3_bucket")
    except ValidationError as e:
        logger.bind(path=secrets).error(e)
        return False
    else:
        return True
