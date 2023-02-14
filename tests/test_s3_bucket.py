from pyaerocom_preproc.config import SECRETS_PATH, settings


def test_credentials():
    if not SECRETS_PATH.is_file():
        raise FileNotFoundError(SECRETS_PATH)

    settings.validators.validate("s3_bucket")
