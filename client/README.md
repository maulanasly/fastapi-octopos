# OctoPOS Client

Flutter client for the FastAPI OctoPOS backend: POS cashier flow (web +
desktop now, Android/iOS scaffolded), manager-lite screens, and offline
sync hooks.

## Run

The backend must be running first:

```bash
make run            # backend on http://localhost:8000
```

Then, from the repo root:

```bash
make client         # Flutter web on http://localhost:3001 (CORS-safe port)
make client-test    # flutter test
make client-analyze # flutter analyze
```

Or directly inside `client/`:

```bash
flutter run -d chrome --web-port=3001
```

The app defaults to `http://127.0.0.1:8000/api/v1` (127.0.0.1, not
`localhost`: Chrome resolves `localhost` to IPv6 `::1` first, and the
dev backend binds IPv4 only). Point the app at a different backend with:

```bash
flutter run -d chrome --web-port=3001 \
  --dart-define=API_BASE_URL=http://192.168.1.50:8000/api/v1
```

## What's implemented

- **Auth**: login/register, JWT access + refresh tokens (silent refresh on
  401, server-side logout revocation). Tokens persist in
  `flutter_secure_storage` on native; on web they fall back to
  localStorage (documented tradeoff).
- **Drawer**: open drawer before selling (required by the backend),
  active-drawer banner, end-of-shift reconciliation with variance display.
- **POS**: category-filtered product grid + search, cart with quantity
  controls, customer picker, promotion code, cash (change preview) or card
  payment, receipt screen. Every order/payment/refund carries a fresh
  `idempotency_key` so double-taps and retries never duplicate.
- **Refunds**: browse recent completed orders, select item quantities,
  create an idempotent refund.
- **Manager-lite**: product & category management (hidden without
  `products:manage`), customer list/create, sales summary + low-stock
  reports (requires `reports:view`).
- **Sync (light)**: catalog delta pull is available via
  `SyncRepository.catalog(since:)`; a full refresh happens on app start
  and via the refresh button. A full offline event queue is a later phase.

## Structure

```
lib/
├── main.dart               # ProviderScope + MaterialApp.router
├── app/
│   ├── router.dart         # go_router, auth redirects, shell
│   └── home_shell.dart     # navigation rail (role-aware)
├── core/
│   ├── config.dart         # API_BASE_URL via --dart-define
│   ├── api_client.dart     # Dio + auth interceptors
│   ├── api_repositories.dart
│   ├── auth_controller.dart
│   ├── models.dart         # pydantic mirrors
│   ├── money.dart          # integer-cents helpers
│   └── token_store.dart
└── features/
    ├── auth/    login_screen
    ├── pos/     pos_screen, cart_controller, catalog_controller,
    │            checkout_sheet, receipt_screen
    ├── drawer/  drawer_controller, reconcile_screen
    ├── refunds/ refund_screen
    ├── catalog/ products_screen
    ├── customers/ customers_screen
    └── reports/ reports_screen
```

## Money

The backend quantizes money to 2 decimals (DECIMAL(12,2)). The client
works in integer cents: `centsFromApi` (backend float -> cents),
`formatCents` (display), `centsToApi` (payload strings). Never do float
arithmetic on money.

## Notes

- `flutter_secure_storage` on web is experimental; web sessions may not
  survive a browser restart.
- Backend CORS allows `http://localhost:3001`; keep the fixed
  `--web-port=3001` when running web locally.
