import sys

if sys.version_info >= (3, 11):
    from importlib import resources
else:
    import importlib_resources as resources

from pathlib import Path

from dynaconf import Dynaconf, Validator

__all__ = ["settings", "SECRETS_PATH"]

SECRETS_PATH = Path("~/.config/pya_pp.toml").expanduser()

with resources.as_file(resources.files(__package__) / "settings.toml") as settings:
    settings = Dynaconf(
        envvar_prefix="PYA_PP",
        settings_files=[settings, SECRETS_PATH],
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
