"""Download the image from S3, read its date, and upload it to S3."""
import json
import os

import boto3

from src.core.prepare_images import get_image_date
from src.secondary_adapters.image_format_readers import WhatImageIFR


def lambda_handler(event, context):
    s3 = boto3.resource("s3")
    input_bucket = s3.Bucket(os.environ["S3_TO_BE_PREPARED_BUCKET"])
    output_bucket = s3.Bucket(os.environ["S3_TO_BE_APPENDED_BUCKET"])

    # Download image from S3
    input_bucket.download_file(
        event["Records"][0]["s3"]["object"]["key"], "/tmp/image.jpg"
    )

    # Read date
    image_date = get_image_date("/tmp/image.jpg", WhatImageIFR).strftime(
        "%Y_%m_%d_%H_%M_%S"
    )

    # Upload to S3 with date as key
    output_bucket.upload_file("/tmp/image.jpg", f"{image_date}.jpg")

    # Delete original image from S3
    input_bucket.delete_objects(
        Delete={
            "Objects": [{"Key": event["Records"][0]["s3"]["object"]["key"]}],
            "Quiet": True,
        }
    )

    return {"statusCode": 200, "body": json.dumps("Hello from Lambda!")}