// k6 load test for FastAPI OctoPOS.
//
// Usage:
//   BASE_URL=http://localhost:8000 VUS=50 DURATION=2m k6 run loadtest/k6-load.js
//
// Env vars:
//   BASE_URL   - API base (default http://localhost:8000)
//   EMAIL      - seed user email (must exist, see loadtest/seed.sh)
//   PASSWORD   - seed user password
//   VUS        - peak virtual users (default 50)
//   DURATION   - steady-state duration (default 2m)
//   SEARCH_Q   - semantic search query text (default "coffee")
//   PROFILE    - label used in the results filename (default dev)

import http from "k6/http";
import { check, group, sleep } from "k6";
import { Counter, Trend } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const EMAIL = __ENV.EMAIL || "loadtest@example.com";
const PASSWORD = __ENV.PASSWORD || "Loadtest123";
const VUS = parseInt(__ENV.VUS || "50", 10);
const DURATION = __ENV.DURATION || "2m";
const SEARCH_Q = __ENV.SEARCH_Q || "coffee";
const PROFILE = __ENV.PROFILE || "dev";

export const ENDPOINTS = [
  "health",
  "auth_token",
  "products_list",
  "products_search",
  "orders_list",
];

// Per-endpoint metrics. Explicit Trends/Counters instead of tag selectors
// because k6 v2 does not expose tagged sub-metrics to handleSummary().
export const epRequests = {};
export const epDuration = {};
for (const ep of ENDPOINTS) {
  epRequests[ep] = new Counter(`ep_requests_${ep}`);
  epDuration[ep] = new Trend(`ep_duration_${ep}`, true);
}

function record(ep, res) {
  epRequests[ep].add(1);
  if (res && res.timings) epDuration[ep].add(res.timings.duration);
}

export const options = {
  scenarios: {
    load: {
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { duration: "30s", target: VUS }, // warm-up ramp
        { duration: DURATION, target: VUS }, // steady state
        { duration: "15s", target: 1 }, // ramp down
      ],
      gracefulRampDown: "10s",
    },
    // /auth/token is rate-limited to 10/minute server-side, so it cannot be
    // load-tested in the main loop. Probe it at ~9 req/min from a single VU
    // to sample real bcrypt-backed login latency instead.
    auth_probe: {
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { duration: "30s", target: 1 },
        { duration: DURATION, target: 1 },
        { duration: "15s", target: 1 },
      ],
      gracefulRampDown: "10s",
      exec: "authProbe",
    },
  },
  summaryTrendStats: ["avg", "min", "med", "p(50)", "p(95)", "p(99)", "max"],
  thresholds: {
    // Baseline-recording mode: sanity gates only, not SLOs.
    http_req_failed: ["rate<0.05"],
    ep_duration_health: ["p(95)<1000"],
    ep_duration_auth_token: ["p(95)<5000"],
    ep_duration_products_list: ["p(95)<5000"],
    ep_duration_products_search: ["p(95)<5000"],
    ep_duration_orders_list: ["p(95)<5000"],
  },
};

function login() {
  const res = http.post(
    `${BASE_URL}/api/v1/auth/token`,
    {
      username: EMAIL,
      password: PASSWORD,
      grant_type: "password",
    },
    {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      tags: { endpoint: "auth_token" },
    },
  );
  record("auth_token", res);
  check(res, {
    "login ok": (r) => r.status === 200,
  }) || console.error(`login failed: ${res.status} ${res.body}`);
  return res.json("access_token");
}

export function setup() {
  const token = login();
  if (!token) {
    throw new Error(
      `Could not authenticate as ${EMAIL}. Run loadtest/seed.sh first.`,
    );
  }
  return { token };
}

export default function (data) {
  const auth = {
    headers: { Authorization: `Bearer ${data.token}` },
  };

  group("health", () => {
    const res = http.get(`${BASE_URL}/api/v1/health`, {
      tags: { endpoint: "health" },
    });
    record("health", res);
  });

  group("products list", () => {
    const res = http.get(`${BASE_URL}/api/v1/products/?limit=50`, {
      ...auth,
      tags: { endpoint: "products_list" },
    });
    record("products_list", res);
    check(res, { "products 200": (r) => r.status === 200 });
  });

  group("products search", () => {
    const res = http.get(
      `${BASE_URL}/api/v1/products/search?q=${encodeURIComponent(SEARCH_Q)}&limit=20`,
      { ...auth, tags: { endpoint: "products_search" } },
    );
    record("products_search", res);
    check(res, {
      "search 200 or 404-no-embeddings": (r) => [200, 404].includes(r.status),
    });
  });

  group("orders list", () => {
    const res = http.get(`${BASE_URL}/api/v1/orders/?limit=50`, {
      ...auth,
      tags: { endpoint: "orders_list" },
    });
    record("orders_list", res);
    check(res, { "orders 200": (r) => r.status === 200 });
  });
}

export function authProbe() {
  sleep(6.7); // ~9 logins/min, under the 10/minute server-side limit
  login();
}

function vals(metric) {
  return metric ? metric.values || metric : null;
}

function endpointRow(data, endpoint) {
  const reqs = vals(data.metrics[`ep_requests_${endpoint}`]);
  const dur = vals(data.metrics[`ep_duration_${endpoint}`]);
  if (!reqs || !dur) return null;
  return {
    endpoint,
    rps: reqs.rate,
    p50: dur["p(50)"],
    p95: dur["p(95)"],
    p99: dur["p(99)"],
    avg: dur.avg,
    max: dur.max,
  };
}

export function handleSummary(data) {
  const rows = ENDPOINTS.map((e) => endpointRow(data, e)).filter(Boolean);
  let table =
    "| endpoint | RPS | avg | p50 | p95 | p99 | max |\n|---|---|---|---|---|---|---|\n";
  for (const r of rows) {
    table += `| ${r.endpoint} | ${r.rps.toFixed(2)} | ${fmt(r.avg)} | ${fmt(r.p50)} | ${fmt(r.p95)} | ${fmt(r.p99)} | ${fmt(r.max)} |\n`;
  }
  const overall = vals(data.metrics.http_req_duration);
  const reqs = vals(data.metrics.http_reqs);
  table += `\nOverall: ${reqs.count} requests, ${reqs.rate.toFixed(1)} req/s, p95 ${fmt(overall["p(95)"])}, p99 ${fmt(overall["p(99)"])}\n`;

  return {
    [`loadtest/results/k6-${PROFILE}-summary.json`]: JSON.stringify(
      data,
      null,
      2,
    ),
    stdout: table,
  };
}

function fmt(ms) {
  return ms == null ? "-" : `${ms.toFixed(1)}ms`;
}
