import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def upload_file_to_s3(file_path, bucket_name, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_path)

    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )

    try:
        s3.upload_file(file_path, bucket_name, object_name)
        print(f"📤 Uploaded {file_path} to s3://{bucket_name}/{object_name}")
    except Exception as e:
        print(f"❌ Error uploading file: {e}")
