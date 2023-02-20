import sys
from getpass import getpass
from pathlib import Path

if sys.version_info >= (3, 11):
    from importlib import resources
else:
    import importlib_resources as resources

import tomli_w
import typer
from dynaconf import Dynaconf, ValidationError, Validator
from loguru import logger

__all__ = ["settings", "config_checker"]

SECRETS_PATH = Path(f"~/.config/{__package__}/config.toml").expanduser()


with resources.as_file(resources.files(__package__) / "settings.toml") as settings:
    settings = Dynaconf(
        envvar_prefix="PYA_PP",
        settings_files=[SECRETS_PATH, settings],
        validators=[
            Validator(
                "s3_bucket.endpoint_url",
                "s3_bucket.bucket_name",
                "s3_bucket.key_id",
                "s3_bucket.access_key",
                must_exist=True,
            )
        ],
    )


def config_checker(
    overwrite: bool = typer.Option(False, "--overwrite", "-O"),
):
    """Check S3 credentials file"""
    if not SECRETS_PATH.exists() or overwrite:
        secrets = {key: getpass(f"{key}: ") for key in ("bucket_name", "key_id", "access_key")}
        SECRETS_PATH.parent.mkdir(True, exist_ok=True)
        SECRETS_PATH.parent.chmod(0o700)  # only user has read/write/execute permissions
        SECRETS_PATH.write_text(tomli_w.dumps({"s3_bucket": secrets}))
        SECRETS_PATH.chmod(0o600)  # only user has read/write permissions

    try:
        settings.validators.validate("s3_bucket")
    except ValidationError as e:
        with logger.contextualize(path=SECRETS_PATH):
            logger.error(e)
        raise typer.Abort()
