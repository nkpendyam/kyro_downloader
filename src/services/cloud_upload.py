"""Cloud upload service for S3 and Google Drive."""
from typing import Any

import os
from pathlib import Path
from src.utils.logger import get_logger
logger = get_logger(__name__)

def upload_to_s3(filepath: str | Path, bucket: str, key: str | None = None, region: str = "us-east-1") -> bool:
    try:
        import boto3
    except ImportError:
        logger.error("boto3 not installed. Run: pip install boto3")
        return False
    path = Path(filepath)
    if not path.exists():
        logger.error(f"File not found: {filepath}")
        return False
    object_key = key or path.name
    try:
        s3 = boto3.client("s3", region_name=region)
        s3.upload_file(str(path), bucket, object_key)
        logger.info(f"Uploaded to S3: s3://{bucket}/{object_key}")
        return True
    except Exception as e:
        logger.error(f"S3 upload failed: {e}")
        return False

def upload_to_gdrive(filepath: str | Path, folder_id: str | None = None, headless: bool = False) -> bool:
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        logger.error("google-api-python-client not installed")
        return False
    path = Path(filepath)
    if not path.exists():
        logger.error(f"File not found: {filepath}")
        return False
    try:
        creds_file = os.environ.get("GOOGLE_CREDENTIALS", "credentials.json")
        if not os.path.exists(creds_file):
            logger.error(f"Google credentials not found: {creds_file}")
            return False
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(creds_file, scopes=["https://www.googleapis.com/auth/drive.file"])
        if headless:
            auth_url, _ = flow.authorization_url(prompt="consent")
            logger.info(f"Visit this URL to authorize: {auth_url}")
            code = input("Enter the authorization code: ")
            flow.fetch_token(code=code)
            creds = flow.credentials
        else:
            creds = flow.run_local_server(port=0)
        service = build("drive", "v3", credentials=creds)
        file_metadata = {"name": path.name}
        if folder_id:
            file_metadata["parents"] = [folder_id]
        media = MediaFileUpload(str(path), resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        logger.info(f"Uploaded to Google Drive: {file.get('id')}")
        return True
    except Exception as e:
        logger.error(f"Google Drive upload failed: {e}")
        return False

def upload_file(filepath: str | Path, provider: str, **kwargs: Any) -> bool:
    if provider == "s3":
        return upload_to_s3(filepath, **kwargs)
    elif provider == "gdrive":
        return upload_to_gdrive(filepath, **kwargs)
    else:
        logger.error(f"Unknown cloud provider: {provider}")
        return False
