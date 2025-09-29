"""ADSB Lookup API (FastAPI

This is a demo service that serves aircraft data from a local CSV and emits simple
structured logs to stdout and Splunk HEC. It is used as the backend for a small
React Native/Expo mobile app.

Key Features:
-------------
- FastAPI for quick API development
- Single CSV-backed data source (no DB, planned AWS connectivity)
- CORS enabled for all origins (lock down later)
- Two endpoints:
    - GET /meta: lightweight heartbeat with row count
    - GET /aircraft: search by callsign or tail number, with limit
- Structured logging to stdout and Splunk HEC (if configured)

Environment Variables:
---------------------
- SPLUNK_HEC_URL: URL of your Splunk HEC endpoint (e.g., https://localhost:8088/services/collector)
- SPLUNK_HEC_TOKEN: Your Splunk HEC token
- SPLUNK_INDEX: (Optional) Splunk index to send events to (e.g.,

Notes
--------------
- Logging must never break availability; errors are swallowed
- CSV is loaded into memory on startup for simplicity; not suitable for large datasets
"""


from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path

# --- Splunk emission & timing ---
# Standard libraries + requests for HTTP emission
import os, time, json, requests

app = FastAPI(title="ADSB Lookup API", version="0.1.0")

# ---------------------------------------------------------------------------
# CORS configuration
# ---------------------------------------------------------------------------
# For a demo/mobile dev scenario we allow any origin/method/headers so the
# Expo/React Native app (or a browser on another device) can call this API
# without preflight/CORS issues. In production, tighten allow_origins to a
# specific list (e.g., your domains) and restrict methods/headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
# The sample data ships with the repo under api/data/adsb_sample.csv.
# Using pathlib keeps path handling robust across OS's.
CSV_PATH = Path(__file__).parent / "data" / "adsb_sample.csv"

# Read CSV once at import time. For large files consider specifying dtypes,
# usecols, or lazy readers. Here we keep it simple; pandas infers types.
df = pd.read_csv(CSV_PATH)

# ---------------------------------------------------------------------------
# Splunk HEC config + emitter
# ---------------------------------------------------------------------------
# These env vars are optional. If not set, emitting to HEC is skipped but we
# still print structured JSON to stdout (useful for local debugging and CI logs).
SPLUNK_HEC_URL   = os.getenv("SPLUNK_HEC_URL")     # e.g. https://localhost:8088/services/collector
SPLUNK_HEC_TOKEN = os.getenv("SPLUNK_HEC_TOKEN")   # your HEC token
SPLUNK_INDEX     = os.getenv("SPLUNK_INDEX")       # optional, e.g., "main"

def emit(event: dict, sourcetype: str = "adsb_api", source: str = "fastapi"):
    """
    Emit a structured event to stdout and to Splunk HEC (if configured).


    Design goals
    ------------
    • Never block the request path for logging. This function is best-effort.
    • Always print locally so developers can see telemetry in their terminal.
    • If HEC config is missing, do nothing (safe no-op) after printing.
    • Suppress all exceptions during network I/O to avoid impacting availability.


    Parameters
    ----------
    event : dict Arbitrary JSON-serializable payload (includes what & context)
    sourcetype : str Splunk sourcetype for event classification
    source : str Logical source label (e.g., component name)
    """
    # Always print locally so you see events in your terminal
    print(json.dumps(event), flush=True)

    # If HEC is not configured, return without network calls
    if not (SPLUNK_HEC_URL and SPLUNK_HEC_TOKEN):
        return  # safe no-op if not configured

    # Construct HEC payload. You can optionally add `host`/`fields` if desired.
    payload = {
        "event": event,
        "sourcetype": sourcetype,
        "source": source,
        "time": time.time(),
    }
    if SPLUNK_INDEX:
        payload["index"] = SPLUNK_INDEX

    try:
        # verify=False is fine for localhost/self-signed dev; use True with real certs
        requests.post(
            SPLUNK_HEC_URL,
            headers={"Authorization": f"Splunk {SPLUNK_HEC_TOKEN}"},
            json=payload,
            timeout=2.0,
            verify=False,
        )
    except Exception:
        # Intentionally swallow errors; logging must not break request handling.
        pass
# -----------------------------------------------

@app.get("/meta")
def meta():
    """Lightweight heartbeat endpoint.
    Returns
    -------
    JSON with dataset row count and a placeholder data freshness value.
    Also emits a small event so we can confirm the API is reachable in logs.
    """
    emit({"event": "meta", "rows": int(len(df)), "status": "ok"})
    return {"rows": int(len(df)), "data_last_updated": "demo-csv"}

@app.get("/aircraft")
def aircraft(
    callsign: str | None = Query(None),
    tail: str | None = Query(None),
    limit: int = 25
):
    """Search for aircraft by exact `callsign` or `tail`.

    Parameters
    ----------
    callsign : str | None
    Exact match (case-insensitive) against the `callsign` column.
    tail : str | None
    Exact match (case-insensitive) against the `tail` column.
    limit : int
    Maximum number of rows to return (applied after filtering).


    Notes
    -----
    • If both `callsign` and `tail` are omitted, this returns the first `limit`
    rows. For a demo this is fine; in production you might enforce at least
    one filter or add pagination.
    • Matching is exact. Consider `.str.contains` with `case=False` for partials.
    """
    t0 = time.time()
    try:
        # Start from the whole DataFrame and apply filters if present.
        d = df
        if callsign:
            d = d[d["callsign"].str.lower() == callsign.lower()]
        if tail:
            d = d[d["tail"].str.lower() == tail.lower()]
        # Trim to the requested limit to bound payload size    
        d = d.head(limit)

        # Normalize/rename selected fields into a clean JSON shape. Handle NaN
        # from pandas by converting to None for JSON compatibility.
        out = []
        for _, r in d.iterrows():
            out.append({
                "callsign": r.get("callsign"),
                "tail": r.get("tail"),
                "icao24": r.get("icao24"),
                "lat": float(r["lat"]) if pd.notna(r["lat"]) else None,
                "lon": float(r["lon"]) if pd.notna(r["lon"]) else None,
                "altitude_m": float(r["baro_altitude_m"]) if pd.notna(r["baro_altitude_m"]) else None,
                "velocity_ms": float(r["velocity_ms"]) if pd.notna(r["velocity_ms"]) else None,
                "last_seen_utc": r.get("last_seen_utc"),
            })

        # Success telemetry: captures what was queried, how long it took, and the
        # size of the returned set. `app_version` is a handy dimension for rollouts.
        emit({
            "event": "aircraft_search",
            "query_type": "callsign" if callsign else "tail" if tail else "none",
            "callsign": callsign,
            "tail": tail,
            "rowcount": len(out),
            "duration_ms": int((time.time() - t0) * 1000),
            "status": "ok",
            "app_version": "demo-0.1",
        })
        return out

    except Exception as e:
        # Error telemetry: include minimal context for triage without leaking
        # sensitive data. Avoid logging request bodies unless necessary.
        emit({
            "event": "error",
            "route": "/aircraft",
            "query_type": "callsign" if callsign else "tail" if tail else "none",
            "callsign": callsign,
            "tail": tail,
            "limit": limit,
            "duration_ms": int((time.time() - t0) * 1000),
            "status": "error",
            "error_type": type(e).__name__,
            "error_msg": str(e),
        })
        # Return a generic 500 to clients; avoid leaking internals in the body.
        raise HTTPException(status_code=500, detail="Internal server error")
