# Mobile Readiness

Status of the backend and client for supporting a mobile POS (tablet/phone)
experience, including offline-first sync. Covers work done on the
`feat/mobile-ready` branch.

## What changed

### Product images (Phase A)

- Images are stored per tenant under `media/{tenant_id}/products/` and are
  served at `/media/...`.
- Uploads are re-encoded to WebP: `<uuid>_orig.webp` (max 1600px, quality 80)
  and `<uuid>_thumb.webp` (max 480px, quality 80). This keeps catalog
  payloads small for slow mobile networks.
- `products.thumbnail_url` column + `thumbnail_url` field in the product API
  schema. Old files are cleaned up on re-upload, image delete, and product
  delete.
- `/media` is served with `Cache-Control: public, max-age=31536000,
  immutable` — filenames are UUIDs, so content never changes under a given
  URL. `gzip` is skipped for `/media` (images are already compressed).
- Validation: max 5 MB, JPEG/PNG/GIF/WebP accepted; everything is re-encoded
  so EXIF metadata is stripped (privacy + size).
- Admin panel: product rows gain an "Upload image" action page
  (`app/templates/product_upload_image.html`).

### Mobile API (Phase B)

- **Auth**: invalid/expired JWTs now return `401` with
  `WWW-Authenticate: Bearer` instead of `403`, so the client can reliably
  trigger re-login. `/auth/token` and refresh responses include
  `expires_in` (seconds) so clients can pre-emptively refresh.
- **Search/filters**:
  - `GET /products` — `q` (name/description), `sku`, `category_id`
  - `GET /customers` — `q` (name/email/phone)
  - `GET /orders` — `status`, `date_from`, `date_to`, `customer_id`;
    ordered by `created_at DESC`
- **Pagination**: `limit` (default 100) is capped at 200; responses include
  an `X-Total-Count` header. The bare-array body shape is unchanged, so the
  existing desktop client keeps working.

### Order concurrency (Phase C)

- `create_order` locks products in ascending `product_id` order, so two
  concurrent carts sharing products cannot deadlock; a second sale of the
  same stock serializes behind the first (`SELECT ... FOR UPDATE`).
- The promotion row is locked with `FOR UPDATE` while its usage count is
  incremented, and the customer row is locked when loyalty points are
  updated — concurrent orders can no longer oversell promotion usage or
  double-redeem points.
- Split payments accept a per-line `idempotency_key`. Retrying an identical
  batch is a no-op; a partially-applied retry returns `409` instead of
  double-charging.

## Queue decision

The order pipeline is synchronous and transactional (stock deduction,
promotion usage, and points are all guarded by row locks). **No FIFO queue
is needed** for the current architecture. A decoupled queue (e.g. Redis
Streams — Redis is already in `docker-compose.yml`) should only be added if
offline-sync ingestion needs to be decoupled from the API, not for order
processing itself.

## Mobile client (Phase D)

- Product tiles and catalog thumbnails use `cached_network_image`, preferring
  the new `thumbnail_url` (falling back to `image_url`) so grids load fast
  and repeat visits are offline-friendly.
- `AppConfig.mediaBaseUrl` (in `client/lib/core/config.dart`) derives the
  media origin from `API_BASE_URL`; override with
  `--dart-define=API_BASE_URL=http://192.168.1.50:8000/api/v1`.
- FastAPI structured 422 responses are rendered per-field
  (`field: message` lines, up to 3) instead of a generic message.

## Remaining gaps for mobile (ranked)

1. **Offline-first sync**: the catalog is fetched live. A mobile flow needs
   a local cache + outbox for orders created offline, replayed against the
   API with the existing idempotency keys (`OrderCreate.idempotency_key`,
   payment `idempotency_key`). The API is already shaped for this.
2. **Delta catalog sync**: add `updated_at` cursor sync
   (`GET /products?updated_since=...`, indexes added in migration 0013) so a
   store tablet can keep the catalog fresh on flaky networks.
3. **Image compression on-device**: thumbnails exist, but the client should
   downscale before upload to reduce bandwidth; the server re-encodes
   anyway, so this is a bandwidth optimization only.
4. **Receipt printing on tablet**: evaluate thermal/Bluetooth printing;
   receipts are already available via `GET /orders/{id}/receipt`.

## Notes

- Mobile-API work is backward compatible; `X-Total-Count` and filter params
  are additive, `thumbnail_url` is a new optional field, and the 401 change
  aligns with OAuth conventions (the old 403 clients accepted a token that
  was actually invalid).
- `orders` are now listed newest-first (`created_at DESC`) — verify no
  client depended on the previous order before merging.
