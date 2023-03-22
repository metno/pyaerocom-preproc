from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dynaconf import Dynaconf
from loguru import logger
from typer import Abort

from .config import config


@lru_cache
def s3_client(settings: Dynaconf):
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_bucket.endpoint_url,
        aws_access_key_id=settings.s3_bucket.access_key_id,
        aws_secret_access_key=settings.s3_bucket.secret_access_key,
    )


def s3_upload(path: Path, *, object_name: str | None = None):
    if (settings := config()) is None:
        raise Abort()
    if object_name is None:
        object_name = path.name
    try:
        s3_client(settings).upload_file(
            path, settings.s3_bucket.bucket_name.strip("s3://"), object_name
        )
    except ClientError as e:
        logger.error(f"{e}, skip")


def s3_list():
    if (settings := config()) is None:
        raise Abort()
    hostname = settings.s3_bucket.bucket_name.strip("s3://")
    objects = s3_client(settings).list_objects_v2(Bucket=hostname)
    for obj in objects["Contents"]:
        print(obj["Key"])
