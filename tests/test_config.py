from pathlib import Path

import pytest
import tomli_w
from dynaconf import Dynaconf, ValidationError
from pyaerocom_preproc.config import _settings, config_checker


@pytest.fixture
def secrets(tmp_path: Path, monkeypatch) -> Path:
    path = tmp_path / "secrets.toml"
    monkeypatch.setattr("pyaerocom_preproc.config.getpass", lambda prompt: prompt.split(":")[0])
    return path


@pytest.fixture
def settings_empty(secrets: Path) -> Dynaconf:
    assert not secrets.exists()
    return _settings(secrets)


@pytest.fixture
def settings(secrets: Path) -> Dynaconf:
    _secrets = ("bucket_name", "access_key_id", "secret_access_key")
    secrets.write_text(tomli_w.dumps({"s3_bucket": {s: s.split("_")[-1] for s in _secrets}}))

    assert secrets.exists()
    return _settings(secrets)


def test_settings(settings: Dynaconf):
    settings.validators.validate("s3_bucket")
    assert settings.s3_bucket.bucket_name == "name"
    assert settings.s3_bucket.access_key_id == "id"
    assert settings.s3_bucket.secret_access_key == "key"
    assert settings.s3_bucket.endpoint_url == "https://rgw.met.no"


def test_settings_fail(settings_empty: Dynaconf):
    with pytest.raises(ValidationError):
        settings_empty.validators.validate("s3_bucket")


def test_config_checker(secrets: Path, settings: Dynaconf):
    assert config_checker(secrets=secrets)
    assert secrets.exists()
    assert settings.s3_bucket.bucket_name == "name"
    assert settings.s3_bucket.access_key_id == "id"
    assert settings.s3_bucket.secret_access_key == "key"
    assert settings.s3_bucket.endpoint_url == "https://rgw.met.no"


def test_config_checker_overwrite(secrets: Path, settings: Dynaconf):
    assert config_checker(secrets=secrets, overwrite=True)
    assert secrets.exists()
    assert settings.s3_bucket.bucket_name == "bucket_name"
    assert settings.s3_bucket.access_key_id == "access_key_id"
    assert settings.s3_bucket.secret_access_key == "secret_access_key"
    assert settings.s3_bucket.endpoint_url == "https://rgw.met.no"


def test_config_checker_input(secrets: Path, settings_empty: Dynaconf):
    config_checker(secrets=secrets)
    assert secrets.exists()
    assert settings_empty.s3_bucket.bucket_name == "bucket_name"
    assert settings_empty.s3_bucket.access_key_id == "access_key_id"
    assert settings_empty.s3_bucket.secret_access_key == "secret_access_key"
    assert settings_empty.s3_bucket.endpoint_url == "https://rgw.met.no"
