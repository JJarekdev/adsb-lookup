from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path

app = FastAPI(title="ADSB Lookup API", version="0.1.0")

# CORS wide-open for demo; lock down later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CSV_PATH = Path(__file__).parent / "data" / "adsb_sample.csv"
df = pd.read_csv(CSV_PATH)

@app.get("/meta")
def meta():
    return {"rows": int(len(df)), "data_last_updated": "demo-csv"}

@app.get("/aircraft")
def aircraft(callsign: str | None = Query(None), tail: str | None = Query(None), limit: int = 25):
    d = df
    if callsign:
        d = d[d["callsign"].str.lower() == callsign.lower()]
    if tail:
        d = d[d["tail"].str.lower() == tail.lower()]
    d = d.head(limit)
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
    return out
