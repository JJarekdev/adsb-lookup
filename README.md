# ADS-B Lookup (Expo + FastAPI)

Demo app that searches aircraft by callsign/tail and shows the last position on a map.

- **Client:** React Native (Expo Router) → see `mobile/README.md` for app-specific notes.
- **API:** FastAPI (CSV-backed) → endpoints `/meta`, `/aircraft`.
- **CI:** Minimal GitHub Actions for both `mobile/` and `api/`.

## Repo layout

adsb-lookup/
├─ mobile/ # Expo app (search, list, detail map)

│ └─ README.md # Expo-specific quickstart (moved here)

└─ api/ # FastAPI service

└─ data/adsb_sample.csv


## Quick start
1) **API**
   ```powershell
   cd api
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   py -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

Visit: http://localhost:8000/meta

    App

        In mobile/app.json set "EXPO_PUBLIC_API_BASE": "http://<YOUR_PC_IP>:8000"

    cd mobile
    npm ci
    npm run start -- --clear

    Open in Expo Go → “Go to ADS-B Search”.

CI

    RN/Expo CI: bundles app (expo export) and uploads artifacts.

    API CI: installs Python deps and runs an import smoke test.

Roadmap

    App: EAS build/submit (gated)

    API: AWS deploy (Lambda/API GW) via Actions OIDC

    Observability: Splunk HEC logs; OTel/Crashlytics + sourcemaps


![RN/Expo CI](https://github.com/JJarekdev/adsb-lookup/actions/workflows/expo-ci.yml/badge.svg)

![API CI](https://github.com/JJarekdev/adsb-lookup/actions/workflows/api-ci.yml/badge.svg)

