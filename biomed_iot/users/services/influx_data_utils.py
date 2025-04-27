"""
High-level data operations (read / delete / export_stream) for a single user bucket.
"""

from __future__ import annotations

import csv
import io
# import zipfile
from datetime import datetime
from typing import Iterator, Dict, Any, Tuple, List

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
        return InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org_id,
            timeout=300_000  # e.g. 5 minutes = 300_000 ms
        )

    # services/influx_data_utils.py  (replace the helper)

    @staticmethod
    def _flatten_tables(flux_tables) -> List[Dict[str, Any]]:
        """
        Convert a sequence of Flux tables into a flat list of row-dicts,
        stripping out Flux metadata and underscore-prefixed keys.
        """
        METADATA_COLUMNS = {"result", "table"}
        flat_rows: List[Dict[str, Any]] = []

        for table in flux_tables:
            for record in table:
                # base fields every row will have
                row: Dict[str, Any] = {
                    "time":  record.get_time().isoformat(),
                    "field": record["_field"],
                    "value": record["_value"],
                }

                # include any non-meta, non-underscore tags/columns
                for column_name, column_value in record.values.items():
                    if column_name in METADATA_COLUMNS or column_name.startswith("_"):
                        continue
                    row[column_name] = column_value

                flat_rows.append(row)

        return flat_rows

    def _row_generator(self, record_stream: Iterator[Any]) -> Iterator[bytes]:
        """
        Take an iterator of FluxRecord, flatten each to a dict,
        write CSV header on first row, then yield each row as UTF-8 bytes.
        """
        buffer = io.StringIO()
        csv_writer: csv.DictWriter | None = None
        header_fields: list[str] | None = None

        for record in record_stream:
            # flatten a single FluxRecord to a simple dict
            row: Dict[str, Any] = {
                "time": record.get_time().isoformat(),
                "field":     record["_field"],
                "value":     record["_value"],
            }
            for key, value in record.values.items():
                if key in {"result", "table"} or key.startswith("_"):
                    continue
                row[key] = value

            # initialize writer & header on first row
            if header_fields is None:
                header_fields = sorted(row.keys())
                csv_writer = csv.DictWriter(buffer, fieldnames=header_fields)
                csv_writer.writeheader()
                yield buffer.getvalue().encode("utf-8")
                buffer.seek(0); buffer.truncate(0)

            # write the current row and yield bytes
            csv_writer.writerow(row)  # type: ignore
            yield buffer.getvalue().encode("utf-8")
            buffer.seek(0); buffer.truncate(0)

        # no records at all?
        if header_fields is None:
            raise ValueError("No matching points")

    # @staticmethod
    # def _csv_zip(records: List[dict], measurement: str) -> Tuple[bytes, str]:
    #     """Return (zip-bytes, filename)."""
    #     fieldnames = sorted(records[0].keys())
    #     buf_csv = io.StringIO()
    #     cw = csv.DictWriter(buf_csv, fieldnames=fieldnames)
    #     cw.writeheader()
    #     cw.writerows(records)

    #     ts = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    #     # ts = timezone.now().strftime("%Y%m%d%H%M%S")
    #     zip_name = f"measurement_{measurement}_{ts}.zip"
    #     buf_zip = io.BytesIO()
    #     with zipfile.ZipFile(buf_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    #         zf.writestr(f"measurement_{measurement}_{ts}.csv", buf_csv.getvalue())
    #     buf_zip.seek(0)
    #     return buf_zip.read(), zip_name


    # ─────────────────────────── Public API ─────────────────────────────────
    def list_measurements(self) -> List[str]:
        """Return all distinct measurement names in this bucket."""
        flux_query = f"""
from(bucket:"{self.bucket}")
  |> range(start: 1970-01-01T00:00:00Z)
  |> keep(columns: ["_measurement"])
  |> distinct(column: "_measurement")
"""
        with self._client() as client:
            tables = client.query_api().query(flux_query)

        # extract the measurement name from each row
        measurements: List[str] = []
        for table in tables:
            for row in table:
                measurements.append(row["_value"])
        return measurements

    def delete(
        self,
        measurement: str,
        tags: Dict[str, str],
        start_iso: str,
        stop_iso: str,
        ) -> bool:
        """
        Delete all points matching the given measurement, tags, and time range.
        Returns True if the HTTP delete succeeded (204 status).
        """
        # build individual clauses like _measurement="foo" and tag1="bar"
        clauses = [f'_measurement="{measurement}"']
        for tag_key, tag_val in tags.items():
            clauses.append(f'{tag_key}="{tag_val}"')
        predicate = " AND ".join(clauses)

        delete_payload = {
            "start":     start_iso,
            "stop":      stop_iso,
            "predicate": predicate,
        }
        endpoint = f"{self.url}/api/v2/delete?org={self.org_id}&bucket={self.bucket}"
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Token {self.token}",
                "Content-Type":  "application/json",
            },
            json=delete_payload,
        )

        return response.status_code == 204

    def export_stream(
        self,
        measurement: str,
        tags: Dict[str, str],
        start_iso: str,
        stop_iso: str,
        ) -> Tuple[Iterator[bytes], str]:
        """
        Stream query results as CSV lines. Returns (csv_byte_iterator, filename).
        """
        # build Flux filter predicate
        filter_clauses = [
            f'r["{tag_name}"]=="{tag_value}"'
            for tag_name, tag_value in tags.items()
        ]
        measurement_predicate = f'r["_measurement"]=="{measurement}"'
        full_predicate = " and ".join([measurement_predicate] + filter_clauses)

        flux = f"""
from(bucket:"{self.bucket}")
  |> range(start:{start_iso}, stop:{stop_iso})
  |> filter(fn:(r) => {full_predicate})
"""

        client = self._client()
        record_stream = client.query_api().query_stream(flux)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"measurement_{measurement}_{timestamp}.csv"

        return self._row_generator(record_stream), filename

#     def export(
#         self,
#         measurement: str,
#         tags: Dict[str, str],
#         start_iso: str,
#         stop_iso: str,
#     ) -> Tuple[bytes, str]:
#         """
#         Query points → return ( zipped-csv bytes, filename ). Raises
#         ValueError when no points match.
#         """
#         tag_filters = " and ".join([f'r["{k}"]=="{v}"' for k, v in tags.items()])
#         fn_pred = f'r["_measurement"]=="{measurement}"' + (
#             f" and {tag_filters}" if tag_filters else ""
#         )

#         flux = f"""
# from(bucket:"{self.bucket}")
#   |> range(start:{start_iso}, stop:{stop_iso})
#   |> filter(fn:(r)=>{fn_pred})
# """
#         with self._client() as c:
#             tables = c.query_api().query(flux)

#         records = self._flatten_tables(tables)
#         if not records:
#             raise ValueError("No matching points")

#         return self._csv_zip(records, measurement)
