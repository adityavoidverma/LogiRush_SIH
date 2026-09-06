# LogiRush — NER Smart Logistics & Accessibility Intelligence Platform

[![CI](https://github.com/AARNAV-ARYA/LogiRush/actions/workflows/ci.yml/badge.svg)](https://github.com/AARNAV-ARYA/LogiRush/actions/workflows/ci.yml)

Disaster-resilient logistics for the eight states of India's North Eastern Region: a routing
and accessibility console for a control room, and a field app for the person standing at the
landslide. Both write to one database, so a report filed on a phone reaches the review queue
the control room is watching.

Built for the Smart India Hackathon.

> **What is real and what is not.** Incident reports, OpenStreetMap place lookups and
> **rainfall** are live — rainfall comes from Open-Meteo, which serves the national weather
> services' own models, and feeds the disaster model and a quarter of every accessibility
> score. It is real meteorological data and it is **not an IMD product**. Corridor landslide
> and flood risk, terrain, and the model's training data are still **sample or synthetic**,
> and nothing here reads an official IMD, GSI, CWC or ASDMA feed. The running app answers this
> input by input at **`/data-sources`**, served from the same module that loads the data. Do
> not present any figure from this system as official government data.

---

## The three pieces

| | What it is | Stack |
|---|---|---|
| [`routeOptimiserBackend/`](routeOptimiserBackend) | API, routing, accessibility scoring, disaster prediction, incident lifecycle | Python · Flask · SQLAlchemy · scikit-learn · NetworkX |
| [`routeOptimiserFrontend/`](routeOptimiserFrontend) | Control-room console — dashboard, network map, planner, review queue | React 19 · Vite · Tailwind v4 · Leaflet |
| [`nerFieldApp/`](nerFieldApp) | Field reporter app — GPS, photo, offline queue | Expo · React Native · expo-router |

`nerLogisticsPlugin/` is a Claude Code plugin exposing the platform over MCP.
[`NER_PLATFORM.md`](NER_PLATFORM.md) is the full engineering write-up: architecture, module
breakdown, the bugs each round found, and the design system.

## What it does

- **Accessibility scoring** — deterministic, ML-free by policy, recomputable by hand:
  `100 − (0.25·weather + 0.30·landslide + 0.20·flood + 0.15·incident + 0.10·delay)`.
- **Risk-aware routing** — multi-objective A\* with Pareto pruning over the corridor graph,
  weighted by cargo profile and urgency. A verified severe blockage removes a corridor.
- **Live rainfall** — real precipitation from Open-Meteo, read at each corridor's midpoint and
  substituted behind the data-provider interface, so it moves the model's features, the
  accessibility score and the chosen route rather than only a weather readout. Falls back to
  the shipped snapshot on any failure, and says which one it is using.
- **Disaster prediction** — the only ML in the platform. An explainable Random Forest that
  predicts disruption probability and nothing else: it does not score accessibility, choose
  routes or verify reports.
- **Community reporting with human verification** — anyone may report, with or without an
  account. Closing a road requires **two different verifiers**, each acting inside their own
  jurisdiction, and every decision is appended to an immutable audit trail.
- **Offline first** — both clients queue reports on the device and sync idempotently on a
  client-generated UUID, so a replayed submission can never duplicate a landslide.

## Run it locally

**Backend** (leave running):

```bash
cd routeOptimiserBackend
pip install -r requirements.txt
python seed_demo_data.py     # optional: demo incidents and shipments
python main.py               # http://localhost:5001
```

**Console:**

```bash
cd routeOptimiserFrontend
npm install
echo "VITE_API_BASE_URL=http://localhost:5001" > .env
npm run dev                  # http://localhost:5173
```

**Field app** — needs your laptop's LAN address so the phone can reach the backend:

```bash
cd nerFieldApp
npm install
echo "EXPO_PUBLIC_API_BASE_URL=http://<your-lan-ip>:5001" > .env
npx expo start               # scan the QR with the iPhone Camera app
```

Sign in as `verifier.as` / `verify123` to review reports, or `controller` / `control123`.
These are **published demo credentials** — see [Deploying](#deploying).

Whole stack against PostgreSQL instead of SQLite: `docker compose up --build`.

## One database, two clients

The console and the field app are not two databases that need syncing — they are two clients
of one backend writing to one `incidents` table. **The entire link is one URL in each:**

| Client | Setting | Value |
|---|---|---|
| Console | `routeOptimiserFrontend/.env` → `VITE_API_BASE_URL` | the backend URL |
| Field app | `nerFieldApp/.env` → `EXPO_PUBLIC_API_BASE_URL` | **the same backend URL** |
| Backend | `DATABASE_URL` | one Postgres URL, on every instance |

Get this wrong and each half works perfectly while showing nothing the other filed. To check
rather than assume: in the app, **Sign in → Test connection** reports the address *and how many
reports that backend holds*. A surprising `0` means you are on the wrong backend.

Every report records which client filed it, so the review queue shows `via field app` on the
row and counts them in the header.

## Deploying

The repository is deploy-ready: [`render.yaml`](render.yaml) is a Render blueprint for the
backend and [`routeOptimiserFrontend/vercel.json`](routeOptimiserFrontend/vercel.json)
configures the console on Vercel. See [DEPLOY.md](DEPLOY.md) for the full walkthrough.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/AARNAV-ARYA/LogiRush)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FAARNAV-ARYA%2FLogiRush&root-directory=routeOptimiserFrontend&project-name=logirush&env=VITE_API_BASE_URL&envDescription=URL%20of%20your%20deployed%20backend%2C%20no%20trailing%20slash)

The short version:

1. **Database** — create a Postgres instance (Neon's free tier is enough) and copy its
   connection string.
2. **Backend → Render** — the button above opens the blueprint. Set `DATABASE_URL`,
   `CORS_ORIGINS` (your console URL) and `NER_DISABLE_DEMO_SEED=1`.
3. **Console → Vercel** — the button above pre-fills the root directory and asks for
   `VITE_API_BASE_URL`; give it the Render URL.
4. **Field app** — set `EXPO_PUBLIC_API_BASE_URL` to the same Render URL, then `npx expo start`
   or `eas build`.

Deploy the backend first: both clients need its URL, and Vercel bakes `VITE_API_BASE_URL` in
at build time.

> **Before a public deployment:** `seed_users.py` ships demo accounts whose passwords are in
> this repository, and the backend seeds them on first run. Anyone who can read the repo can
> then sign in as a controller and close roads. Set **`NER_DISABLE_DEMO_SEED=1`** and create a
> real roster, and set `CORS_ORIGINS` to your console's origin rather than leaving it `*`.

## Tests

```bash
cd routeOptimiserBackend && python -m pytest    # 165 tests
cd routeOptimiserFrontend && npm run build
python e2e/test_e2e.py --base-url http://127.0.0.1:4173 --api-url http://127.0.0.1:5001
```

CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs all three on every push,
including a real browser against a real backend.

## Licence and data

Sample road, terrain and risk data in `routeOptimiserBackend/data/raw/ner/` is illustrative and
documented as such in each file's header. Place search uses OpenStreetMap via Photon and
Overpass; OSM data is ODbL-licensed and attribution is carried in every response.
