"""
Google Drive connector — downloads data files for ingestion.

Requires: pip install google-api-python-client google-auth-oauthlib
"""
import io
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional

log = logging.getLogger(__name__)

# MIME types we can ingest
DATA_MIMES = (
    "mimeType='text/csv' or "
    "mimeType='application/json' or "
    "mimeType='application/xml' or "
    "mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or "
    "mimeType='application/vnd.ms-excel'"
)


class GoogleDriveClient:

    def __init__(self, credentials_path: str = None):
        self._creds_path = credentials_path or os.getenv("GOOGLE_CREDENTIALS_PATH", "")
        self._service = None

    def authenticate(self) -> bool:
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError:
            log.error("Google API packages not installed — "
                      "run: pip install google-api-python-client google-auth-oauthlib")
            return False

        scopes = ["https://www.googleapis.com/auth/drive.readonly"]
        token_file = Path(self._creds_path).parent / "token.json"
        creds = None

        if token_file.exists():
            creds = Credentials.from_authorized_user_file(str(token_file), scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self._creds_path or not Path(self._creds_path).exists():
                    log.error("Google credentials file not found")
                    return False
                flow = InstalledAppFlow.from_client_secrets_file(self._creds_path, scopes)
                creds = flow.run_local_server(port=0)

            token_file.write_text(creds.to_json())

        self._service = build("drive", "v3", credentials=creds)
        log.info("Google Drive authenticated")
        return True

    def list_files(self, max_results: int = 25) -> List[Dict]:
        if not self._service:
            return []
        result = self._service.files().list(
            q=DATA_MIMES, pageSize=max_results,
            fields="files(id, name, mimeType, size, modifiedTime)",
        ).execute()
        return result.get("files", [])

    def download(self, file_id: str, dest_dir: str) -> Optional[str]:
        if not self._service:
            return None
        from googleapiclient.http import MediaIoBaseDownload

        meta = self._service.files().get(fileId=file_id).execute()
        out = Path(dest_dir) / meta.get("name", f"download_{file_id}")
        out.parent.mkdir(parents=True, exist_ok=True)

        request = self._service.files().get_media(fileId=file_id)
        with io.FileIO(str(out), "wb") as fh:
            dl = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = dl.next_chunk()

        log.info("Downloaded %s", out)
        return str(out)
