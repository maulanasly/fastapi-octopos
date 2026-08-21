# API Load Tests

k6-based load testing for the FastAPI OctoPOS backend, recording throughput
(RPS), latency percentiles (p50/p95/p99), and backend container memory (RSS)
under load.

## Layout

| File | Purpose |
|---|---|
| `k6-load.js` | Load scenarios: `health`, `products_list`, `products_search` (pgvector), `orders_list` in a ramping-VU loop, plus a separate 1-VU `auth_probe` pacing logins under the server-side 10/min rate limit on `/auth/token`. Per-endpoint RPS + latency via explicit Trend/Counter metrics; JSON summary written to `results/`. |
| `seed.sh` | Idempotent seeding over the API: registers a tenant-owner user (`loadtest@example.com` / `Loadtest123`), then tops up to `PRODUCTS` (default 100), `CUSTOMERS` (30), `ORDERS` (50). Opens a drawer session first — orders require one. |
| `rss_sampler.sh` | Samples the backend container's RSS + CPU% once per second into a CSV; prints avg/max on exit. |
| `run.sh` | Orchestrates seed → sampler → k6 → combined summary. |

## Usage

```bash
# against a running stack (dev or prod-like), defaults: PROFILE=dev VUS=50 DURATION=2m
make loadtest PROFILE=dev

# custom run
BASE_URL=http://localhost:8000 VUS=25 DURATION=90s ./loadtest/run.sh myprofile
```

Start the stack first: `make docker-dev` (dev) or `make docker-up`
(prod-like image, no `--reload`). Both currently run **one uvicorn worker**
(`docker/entrypoint.sh`).

## Method

- Warm-up ramp 30s → steady state `DURATION` → ramp-down 15s.
- Login once in `setup()`; requests carry a bearer token.
- `/auth/token` cannot be loop-tested (rate-limited to 10/min by design);
  the probe samples real bcrypt-backed login latency at ~9 req/min.
- RSS sampled from `docker stats octopos-backend` every 1s during the run.
- Thresholds are sanity gates only (baseline-recording mode), not SLOs.
- Generator and server share one host (loopback), so absolute numbers include
  some CPU-contention noise; cross-profile comparisons remain valid.

## Baseline results (2026-08-21)

Machine: Pop!_OS 24.04, 16 CPUs, 30 GiB RAM · k6 v2.2.0 · postgres pgvector:pg16,
redis 7, backend container (1 uvicorn worker) · seeded DB (100 products / 30 customers / 50 orders)

### Dev stack (`make docker-dev`, uvicorn --reload), 10 VUs / 1m

| endpoint | RPS | avg | p50 | p95 | p99 | max |
|---|---|---|---|---|---|---|
| health | 22.99 | 9.7ms | 6.3ms | 25.9ms | 80.1ms | 116.7ms |
| auth_token (probe) | 0.15 | 283.1ms | 280.4ms | 372.9ms | 375.1ms | 375.7ms |
| products_list | 22.99 | 79.9ms | 77.1ms | 170.1ms | 196.4ms | 243.6ms |
| products_search | 22.99 | 72.7ms | 69.7ms | 158.4ms | 187.5ms | 236.4ms |
| orders_list | 22.99 | 164.0ms | 168.2ms | 278.1ms | 300.5ms | 337.6ms |

Overall: 10,321 req, 92.1 req/s, p95 236.6ms, p99 283.5ms — RSS avg 148.0 MiB, max 152.3 MiB

### Prod-like stack (`make docker-up`), 10 VUs / 1m

| endpoint | RPS | avg | p50 | p95 | p99 | max |
|---|---|---|---|---|---|---|
| health | 24.35 | 9.2ms | 6.2ms | 25.0ms | 76.0ms | 105.8ms |
| auth_token (probe) | 0.15 | 302.9ms | 305.7ms | 372.1ms | 374.7ms | 375.3ms |
| products_list | 24.35 | 80.1ms | 79.1ms | 166.2ms | 195.6ms | 236.7ms |
| products_search | 24.35 | 73.3ms | 71.3ms | 156.7ms | 189.7ms | 230.8ms |
| orders_list | 24.35 | 164.9ms | 171.1ms | 272.3ms | 291.5ms | 323.3ms |

Overall: 10,280 req, 97.6 req/s, p95 233.6ms, p99 278.8ms — RSS avg 155.3 MiB, max 156.3 MiB

### Dev stack, 50 VUs / 2m (saturated)

| endpoint | RPS | avg | p50 | p95 | p99 | max |
|---|---|---|---|---|---|---|
| health | 21.78 | 34.8ms | 29.4ms | 108.1ms | 139.1ms | 165.6ms |
| auth_token (probe) | 0.14 | 867.8ms | 817.8ms | 2013.2ms | 2361.0ms | 2439.1ms |
| products_list | 21.78 | 610.5ms | 667.3ms | 1145.1ms | 1404.6ms | 1761.3ms |
| products_search | 21.78 | 599.1ms | 651.6ms | 1149.6ms | 1541.9ms | 2544.0ms |
| orders_list | 21.78 | 722.5ms | 769.8ms | 1292.6ms | 1658.4ms | 2591.1ms |

Overall: 14,607 req, 87.3 req/s, p95 1131.0ms, p99 1444.9ms — RSS avg 186.0 MiB, max 194 MiB

### Prod-like stack, 50 VUs / 2m (saturated)

| endpoint | RPS | avg | p50 | p95 | p99 | max |
|---|---|---|---|---|---|---|
| health | 22.68 | 32.8ms | 27.9ms | 93.7ms | 119.3ms | 140.3ms |
| auth_token (probe) | 0.14 | 674.0ms | 786.7ms | 956.0ms | 988.7ms | 997.1ms |
| products_list | 22.68 | 575.0ms | 622.3ms | 1079.5ms | 1349.6ms | 2061.2ms |
| products_search | 22.68 | 567.8ms | 609.7ms | 1094.9ms | 1508.2ms | 2412.1ms |
| orders_list | 22.68 | 681.9ms | 726.8ms | 1202.4ms | 1511.6ms | 2180.7ms |

Overall: 15,472 req, 90.9 req/s, p95 1061.6ms, p99 1357.2ms — RSS avg 150.9 MiB, max 160.2 MiB

## Observations

- **Single-worker ceiling ≈ 90–97 req/s aggregate** (~23 RPS per endpoint across
  the four loop endpoints). Throughput barely changes between 10 and 50 VUs;
  latency absorbs the extra load instead (p95 235ms → 1100ms+).
- **The knee is between 10 and 20 VUs** for this workload mix; beyond it,
  queueing dominates. Prod-like and dev numbers are nearly identical —
  `--reload` costs little once warm.
- **Login (bcrypt) is the most expensive path**: ~280–305ms median even at
  light load, degrading to ~0.8–2s p95 under saturation. It is also
  deliberately rate-limited to 10/min.
- **Memory is flat and healthy**: RSS stays in the 148–194 MiB band across all
  runs with no upward drift within a run.
- Semantic search (`products/search`) is *not* heavier than the plain list
  endpoint at this data size (embeddings fallback path vs. indexed KNN).

## Granian vs uvicorn (2026-08-21, resource-constrained)

Target deployment simulated via `docker-compose.limits.yml`: backend capped at
**1.5 CPUs / 1 GiB**, postgres **0.5 CPUs / 768 MiB** (2 CPU / 2 GB box shared
between API and DB). Prod-like stack, seeded DB.

| config | VUs | RPS | p50 | p95 | p99 | RSS avg/max |
|---|---|---|---|---|---|---|
| uvicorn 1w | 10 | 75.3 | — | 366ms | 575ms | 119 / 125 MiB |
| granian 1w | 10 | **99.5** (+32%) | — | **235ms** (-36%) | **280ms** | 139 / 144 MiB |
| uvicorn 1w | 50 | 58.6 | — | 1793ms | 2376ms | 150 / 158 MiB |
| granian 1w | 50 | **94.7** (+62%) | — | **1080ms** (-40%) | **1462ms** | 174 / 181 MiB |
| granian 2w | 10 | **141.2** | — | **186ms** | **262ms** | 227 / 234 MiB |
| granian 2w | 50 | **127.3** (+2.7% vs uv) | — | 802ms | 1066ms | 276 / 286 MiB |
| uvicorn 2w | 50 | 123.9 | — | **762ms** (-5%) | **972ms** (-9%) | 295 / 307 MiB |

**Decision: granian is now the default server** (`SERVER` env in
`docker/entrypoint.sh`, `granian==2.8.1` in requirements.txt; uvicorn stays
installed as fallback).

Rationale:
- At the memory-tight 1-worker setting granian is dramatically better
  (+32–62% RPS, -36–40% tail latency).
- At 2 workers throughput is a wash (+2.7% granian) and tails are within
  ~5–9% in uvicorn's favor — effectively noise once postgres (0.5 CPU)
  becomes the bottleneck.
- Granian's RSS is lower in the multi-worker configs that fit the 2 GB budget.

Operational notes:
- Scale with `WEB_CONCURRENCY` (default 1). For the 2 CPU / 2 GB target,
  `WEB_CONCURRENCY=2` fits comfortably (~286 MiB max + 768 MiB postgres).
- SSE (`/orders/serving/stream`) and slowapi rate limiting verified working
  under granian before benchmarking.
- Dev mode (`UVICORN_RELOAD=1`, despite the legacy name) passes `--reload`
  to either server.

## Follow-ups

- Add write-path scenarios (POST orders with payment) once targets are set.
- Convert observations into SLO thresholds in `k6-load.js` (e.g. p95 < 500ms
  at 20 VUs) so regressions fail CI-style runs.
