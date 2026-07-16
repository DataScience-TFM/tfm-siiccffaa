from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from .config import DATA_DIR, LOCATION, PROJECT_ID


BIGQUERY_SCOPE = "https://www.googleapis.com/auth/bigquery"
BIGQUERY_API = "https://bigquery.googleapis.com/bigquery/v2"


class BigQueryRunner:
    """Ejecuta SQL mediante la API REST HTTPS de BigQuery, sin Google Cloud SDK."""

    def __init__(self, project_id: str = PROJECT_ID, location: str = LOCATION) -> None:
        self.project_id = project_id
        self.location = location
        self.credentials = self._load_credentials()
        self.session = requests.Session()

    @staticmethod
    def _load_credentials():
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            env_file = Path(__file__).resolve().parents[1] / ".env"
            if env_file.is_file():
                for raw_line in env_file.read_text(encoding="utf-8-sig").splitlines():
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    name, value = line.split("=", 1)
                    if name.strip() == "GOOGLE_APPLICATION_CREDENTIALS":
                        credentials_path = value.strip().strip('"').strip("'")
                        break
        if not credentials_path:
            raise RuntimeError(
                "Falta GOOGLE_APPLICATION_CREDENTIALS. Defina la variable o "
                "revise el archivo .env de la raíz del proyecto."
            )
        path = Path(credentials_path).expanduser()
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[1] / path
        path = path.resolve()
        if not path.is_file():
            raise FileNotFoundError(f"No existe el archivo de credenciales: {path}")
        return service_account.Credentials.from_service_account_file(
            path, scopes=[BIGQUERY_SCOPE]
        )

    def _headers(self) -> dict[str, str]:
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return {
            "Authorization": f"Bearer {self.credentials.token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def _request(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        response = self.session.request(
            method, url, headers=self._headers(), timeout=210, **kwargs
        )
        if not response.ok:
            try:
                detail = response.json().get("error", {}).get("message", response.text)
            except ValueError:
                detail = response.text
            raise RuntimeError(f"BigQuery REST {response.status_code}: {detail}")
        return response.json()

    @staticmethod
    def _rows_to_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
        fields = payload.get("schema", {}).get("fields", [])
        names = [field["name"] for field in fields]
        records = []
        for row in payload.get("rows", []):
            values = [cell.get("v") for cell in row.get("f", [])]
            records.append(dict(zip(names, values)))
        return records

    def query_to_dataframe(self, sql: str) -> pd.DataFrame:
        url = f"{BIGQUERY_API}/projects/{self.project_id}/queries"
        payload = self._request(
            "POST",
            url,
            json={
                "query": sql,
                "useLegacySql": False,
                "location": self.location,
                "timeoutMs": 200000,
                "maxResults": 10000,
            },
        )
        job = payload.get("jobReference", {})
        job_id = job.get("jobId")
        if not job_id:
            raise RuntimeError("BigQuery no devolvió un identificador de trabajo.")

        while not payload.get("jobComplete", False):
            time.sleep(1)
            payload = self._get_results(job_id)

        records = self._rows_to_records(payload)
        page_token = payload.get("pageToken")
        while page_token:
            page = self._get_results(job_id, page_token)
            records.extend(self._rows_to_records(page))
            page_token = page.get("pageToken")

        columns = [
            field["name"] for field in payload.get("schema", {}).get("fields", [])
        ]
        return pd.DataFrame(records, columns=columns or None)

    def _get_results(self, job_id: str, page_token: str | None = None) -> dict[str, Any]:
        url = f"{BIGQUERY_API}/projects/{self.project_id}/queries/{job_id}"
        params: dict[str, Any] = {
            "location": self.location,
            "maxResults": 10000,
            "timeoutMs": 200000,
        }
        if page_token:
            params["pageToken"] = page_token
        return self._request("GET", url, params=params)

    def save_query(self, name: str, sql: str) -> pd.DataFrame:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        frame = self.query_to_dataframe(sql)
        frame.to_csv(DATA_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
        return frame
