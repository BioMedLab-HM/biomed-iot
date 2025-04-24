"""
High-level data operations (read / delete / export) for a single user bucket.
"""

from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime
from typing import Dict, List, Tuple

import requests
from influxdb_client import InfluxDBClient

from biomed_iot.config_loader import config


def to_rfc3339(value) -> str:
    """Return RFC-3339 string, *always* suffixed with 'Z'."""
    if isinstance(value, datetime):
        return value.isoformat() + "Z"
    if isinstance(value, str):
        return value if value.endswith("Z") else value + "Z"
    raise TypeError(f"Unsupported timestamp type: {type(value)}")


class InfluxDataManager:
    """
    Encapsulates InfluxDB calls for a user’s personal bucket
    (querying, deleting and exporting data).
    """

    def __init__(self, user):
        self.user = user
        self.org_id = config.influxdb.INFLUX_ORG_ID
        self.url = f"http://{config.influxdb.INFLUX_HOST}:{config.influxdb.INFLUX_PORT}"
        self.bucket = user.influxuserdata.bucket_name
        self.token = user.influxuserdata.bucket_token

    # ─────────────────────────── Private helpers ────────────────────────────
    def _client(self) -> InfluxDBClient:
        return InfluxDBClient(url=self.url, token=self.token, org=self.org_id)

    # services/influx_data_utils.py  (replace the helper)

    @staticmethod
    def _flatten_tables(tables) -> List[dict]:
        """
        Convert Flux tables to list[dict] while stripping Flux-meta columns
        and any tag keys you don't want (e.g. 'fieldname').
        """
        SKIP = {"result", "table"}          # Flux meta cols
        rows = []
        for table in tables:
            for rec in table:
                row = {
                    "_time":  rec.get_time().isoformat(),
                    "_field": rec["_field"],
                    "_value": rec["_value"],
                }
                for k, v in rec.values.items():
                    if k in SKIP or k.startswith("_"):
                        continue
                    row[k] = v
                rows.append(row)
        return rows


    @staticmethod
    def _csv_zip(records: List[dict], measurement: str) -> Tuple[bytes, str]:
        """Return (zip-bytes, filename)."""
        fieldnames = sorted(records[0].keys())
        buf_csv = io.StringIO()
        cw = csv.DictWriter(buf_csv, fieldnames=fieldnames)
        cw.writeheader()
        cw.writerows(records)

        ts = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        # ts = timezone.now().strftime("%Y%m%d%H%M%S")
        zip_name = f"measurement_{measurement}_{ts}.zip"
        buf_zip = io.BytesIO()
        with zipfile.ZipFile(buf_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"measurement_{measurement}_{ts}.csv", buf_csv.getvalue())
        buf_zip.seek(0)
        return buf_zip.read(), zip_name

    # ─────────────────────────── Public API ─────────────────────────────────
    def list_measurements(self) -> List[str]:
        """Return all distinct measurement names for the user bucket."""
        flux = f"""
from(bucket:"{self.bucket}")
  |> range(start: 1970-01-01T00:00:00Z)
  |> keep(columns:["_measurement"])
  |> distinct(column:"_measurement")
"""
        with self._client() as c:
            res = c.query_api().query(flux)
        return [row["_value"] for table in res for row in table]

    def delete(
        self,
        measurement: str,
        tags: Dict[str, str],
        start_iso: str,
        stop_iso: str,
    ) -> bool:
        """Delete records; return True on success."""
        predicate_parts = [f'_measurement="{measurement}"'] + [
            f'{k}="{v}"' for k, v in tags.items()
        ]
        predicate = " AND ".join(predicate_parts)

        payload = {"start": start_iso, "stop": stop_iso, "predicate": predicate}
        url = f"{self.url}/api/v2/delete?org={self.org_id}&bucket={self.bucket}"
        resp = requests.post(
            url,
            headers={"Authorization": f"Token {self.token}", "Content-Type": "application/json"},
            json=payload,
        )
        return resp.status_code == 204

    def export(
        self,
        measurement: str,
        tags: Dict[str, str],
        start_iso: str,
        stop_iso: str,
    ) -> Tuple[bytes, str]:
        """
        Query points → return ( zipped-csv bytes, filename ). Raises
        ValueError when no points match.
        """
        tag_filters = " and ".join([f'r["{k}"]=="{v}"' for k, v in tags.items()])
        fn_pred = f'r["_measurement"]=="{measurement}"' + (
            f" and {tag_filters}" if tag_filters else ""
        )

        flux = f"""
from(bucket:"{self.bucket}")
  |> range(start:{start_iso}, stop:{stop_iso})
  |> filter(fn:(r)=>{fn_pred})
"""
        with self._client() as c:
            tables = c.query_api().query(flux)

        records = self._flatten_tables(tables)
        if not records:
            raise ValueError("No matching points")

        return self._csv_zip(records, measurement)
