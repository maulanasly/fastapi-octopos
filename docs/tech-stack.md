[Back to README](../README.md)

# Tech Stack

- **Backend:** FastAPI
- **ORM:** SQLAlchemy
- **Database:** PostgreSQL 16 + pgvector (`pgvector/pgvector:pg16` image; dev stack on `localhost:5433`)
- **Geo:** native `point` + GiST `point_ops` KNN, `earthdistance`+`cube` for radius queries
- **Embeddings:** pgvector `vector(384)` + HNSW index; providers `hash` (offline) / `api` (OpenAI-compatible)
- **Migrations:** Alembic
- **Auth:** JWT (`python-jose`) + bcrypt hashing
- **Rate Limiting:** SlowAPI
- **Admin UI:** SQLAdmin
- **Client:** Flutter (web-first) with `flutter_map` (OpenStreetMap), `latlong2`, `geolocator`
