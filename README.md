# PolicyLab

**Cloud-based reproducible research platform for public policy datasets.**

Run housing, labor, demographic, and live World Bank analyses reproducibly —
backed by Ray distributed compute, full observability, and a locked
reproducibility manifest on every run.

---

## What it does

A researcher can:

1. **Browse datasets** — ACS housing, BLS labor, Census, World Bank, HUD FMR, and more
2. **Submit experiments** — choose a dataset, analysis type, and parameters (or pick live World Bank indicators from a curated catalog)
3. **Distributed execution** — job dispatches to a Ray worker process with real CPU/memory profiling
4. **Track results** — live-updating job logs, CPU/memory charts over runtime, structured output visualizations
5. **Reproduce any run** — every experiment locks git commit, environment hash, dataset version, parameter fingerprint, and Python version

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Recharts |
| Backend | Python 3.11, FastAPI, SQLAlchemy |
| Distributed compute | **Ray** (local mode → scales to cluster) |
| Database | SQLite (dev) / PostgreSQL (Docker / prod) |
| Metrics | Prometheus + Grafana |
| Containers | Docker Compose |

---

## Quick start

### Option A — Docker Compose (recommended)

```bash
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 (admin / admin) |

### Option B — Bare metal

Requires Python 3.11+ and Node 20+.

```bash
./dev.sh
```

Opens:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  React Dashboard (Vite + Tailwind)                          │
│  • Dataset browser   • New experiment form                  │
│  • Live job monitor  • CPU/memory charts  • Repro manifest  │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST  /api/v1/*
┌──────────────────────▼──────────────────────────────────────┐
│  FastAPI Backend                                            │
│  • /experiments   • /jobs   • /datasets   • /metrics       │
│  • Background job monitor (polls Ray futures every 2s)     │
│  • Prometheus metrics endpoint                             │
└────────────────┬────────────────────────────────────────────┘
                 │ ray.remote()
┌────────────────▼────────────────────────────────────────────┐
│  Ray Worker Process                                         │
│  • Isolated execution (separate process / node)            │
│  • psutil CPU/memory sampling every step                   │
│  • Simulated GPU metrics (swap pynvml for real hardware)   │
│  • Returns: artifacts + per-step metrics + repro manifest  │
└─────────────────────────────────────────────────────────────┘
                 │ stores results
┌────────────────▼────────────────────────────────────────────┐
│  SQLite / PostgreSQL                                        │
│  datasets · experiments · jobs · job_metrics · artifacts   │
└─────────────────────────────────────────────────────────────┘
```

### Reproducibility manifest

Every experiment automatically records:

```json
{
  "job_id": "...",
  "analysis_type": "housing_affordability",
  "dataset_id": "acs-housing-2023",
  "parameters_hash": "a3f9c12e",
  "python_version": "3.11.9",
  "platform": "Linux-6.1...",
  "ray_version": "2.38.0",
  "executed_at_utc": "2025-05-15T14:23:11",
  "total_runtime_seconds": 1.842
}
```

The backend also records at the experiment level:

- `git_commit` — short SHA of the code at submission time
- `environment_hash` — SHA-256 of the full pip freeze output
- `dataset_version` — hash of the dataset identifier
- `container_image` — Docker image tag

Re-running with the same manifest + parameters produces byte-identical results for seeded analyses. World Bank runs fetch live data, so results reflect whatever the API returns at execution time — the manifest records exactly which indicators and parameters were used.

---

## Available analyses

### World Bank Development & Climate Indicators — live data
- Source: [World Bank Open Data API](https://data.worldbank.org/) via `wbgapi` (no API key required)
- Researcher picks any combination of indicators from a curated catalog of 18 across 6 categories
- Returns one time-series chart per indicator (pivoted by country) + a latest-snapshot comparison table
- Parameters: `countries`, `year_start`, `year_end`, `indicators` (list of WB codes)

**Indicator catalog:**

| Category | Indicators |
|---|---|
| Economy | GDP per capita, GDP growth, Inflation, Government debt, Trade openness |
| Social | GINI inequality, Unemployment, Urban population, Fertility rate |
| Health | Life expectancy, Child mortality, Health expenditure |
| Education | Education expenditure, Internet users |
| Energy & Climate | Energy use per capita, Renewable energy share, Electricity access |
| Demographics | Total population |

### Housing Affordability
- Source: American Housing Survey (ACS)
- Cost burden rates (>30% / >50% of income on housing) by state and income quintile
- Year-over-year trend by quintile
- Parameters: `states`, `year_start`, `year_end`

### Labor Market Trends
- Source: BLS Current Population Survey
- Unemployment by industry sector (U-3 and U-6), education-level premium
- Parameters: `sectors`, `year_start`, `year_end`, `measure`

### Census Demographics
- Source: 2020 Decennial Census
- Age pyramid, race/ethnicity composition, state-level population breakdown
- Parameters: `states`, `breakdown`

---

## Observability

Prometheus scrapes `/api/v1/metrics/prometheus` every 15s:

- `policylab_jobs_submitted_total`
- `policylab_jobs_completed_total{status}`
- `policylab_job_duration_seconds` (histogram)
- `policylab_active_jobs` (gauge)
- `policylab_host_cpu_percent` / `policylab_host_memory_mb`

Grafana at `:3001` with Prometheus pre-provisioned as data source.

---

## Scaling to a real cluster

The job runner is a standard `@ray.remote` function. Switching to a remote cluster:

```python
ray.init(address="ray://my-cluster:10001")
```

For GPU profiling, swap the simulated metrics with `pynvml` / NVIDIA DCGM in `worker/runner.py`.

---

## Project layout

```
policy-lab/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app + background job monitor
│   │   ├── models.py        # SQLAlchemy schema
│   │   ├── schemas.py       # Pydantic I/O models
│   │   ├── seeds.py         # Dataset catalog
│   │   └── routers/         # experiments · jobs · datasets · metrics
│   └── worker/
│       ├── runner.py        # Ray remote task + thread-pool fallback
│       └── analyses/        # housing · labor · census · world_bank
├── frontend/
│   └── src/
│       ├── pages/           # Dashboard · Datasets · NewExperiment · ExperimentDetail
│       └── components/      # Layout · MetricsChart · ReproManifest · JobStatusBadge
├── infra/
│   ├── prometheus/
│   └── grafana/
├── docker-compose.yml
├── dev.sh                   # Bare-metal dev launcher
└── .env.example
```