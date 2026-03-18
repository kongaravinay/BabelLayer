"""
Generic REST API connector for pulling data into DataFrames.
"""
import requests
import pandas as pd
import logging
from typing import Optional, Any

log = logging.getLogger(__name__)


class RestClient:

    def __init__(self, base_url: str, *, token: str = None,
                 headers: dict = None, timeout: int = 30):
        self._url = base_url.rstrip("/")
        self._headers = headers or {}
        self._timeout = timeout
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    def get_json(self, endpoint: str = "", params: dict = None) -> Optional[Any]:
        url = f"{self._url}/{endpoint.lstrip('/')}" if endpoint else self._url
        try:
            r = requests.get(url, headers=self._headers, params=params, timeout=self._timeout)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as exc:
            log.error("GET %s failed: %s", url, exc)
            return None

    def to_dataframe(self, endpoint: str = "", params: dict = None,
                     records_path: str = None) -> Optional[pd.DataFrame]:
        """Fetch JSON and convert to DataFrame.  `records_path` is a dot-separated
        key path like 'data.results' to reach the array of records."""
        data = self.get_json(endpoint, params)
        if data is None:
            return None

        if records_path:
            for key in records_path.split("."):
                data = data[key]

        if isinstance(data, list):
            return pd.DataFrame(data)
        if isinstance(data, dict):
            return pd.DataFrame([data])

        log.error("Response is not a list or dict")
        return None

    def ping(self) -> bool:
        try:
            r = requests.head(self._url, headers=self._headers, timeout=self._timeout)
            return r.status_code < 400
        except requests.RequestException:
            return False
