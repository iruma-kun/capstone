import json
import urllib.parse

import boto3

s3_client = boto3.client("s3")


def lambda_handler(event, context):
    """
    AWS Lambda function triggered automatically when a corporate document
    is uploaded to the Amazon S3 compliance data lake.
    """
    print("Received S3 upload event:", json.dumps(event, indent=2))

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"], encoding="utf-8")

        print(f"Processing new document upload from S3 bucket '{bucket}', key: '{key}'")

        try:
            # Fetch object metadata or content from S3
            response = s3_client.get_object(Bucket=bucket, Key=key)
            file_content = response["Body"].read()

            print(
                f"Successfully retrieved document {key} ({len(file_content)} bytes). Routing to compliance engine..."
            )

            # In production, this forwards the extracted text to our FastAPI compliance microservices

        except Exception as e:
            print(f"Error processing S3 object {key}: {str(e)}")
            raise e

    return {
        "statusCode": 200,
        "body": json.dumps("Document compliance audit pipeline executed successfully."),
    }
