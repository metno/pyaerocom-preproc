# import boto
# import boto.s3.connection
import logging
import os
import sys

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# By default load_dotenv will look for the .env file in the current working directory or any parent directories
load_dotenv()

access_key = os.getenv("S3_BUCKET_ACCESS_KEY")
secret_key = os.getenv("S3_BUCKET_SECRET_KEY")

bucketname = "cams282-user5"

if len(sys.argv) != 2:
    raise ValueError("Please provide the path to the file to be uploaded")

pathtofile = sys.argv[1]
objectname = os.path.basename(pathtofile)


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client(
        "s3",
        endpoint_url="https://rgw.met.no",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
        print("OK")
    except ClientError as e:
        logging.error(e)
        return False
    return True


upload_file(pathtofile, bucketname, objectname)
