from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from loguru import logger

from .config import config_checker, settings


@lru_cache
def s3_client():
    config_checker()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_bucket.endpoint_url,
        aws_access_key_id=settings.s3_bucket.access_key_id,
        aws_secret_access_key=settings.s3_bucket.secret_access_key,
    )


def s3_upload(path: Path, *, object_name: str | None = None):
    if object_name is None:
        object_name = path.name

    try:
        s3_client().upload_file(path, settings.s3_bucket.bucket_name, object_name)
    except ClientError as e:
        logger.error(f"{e}, skip")
