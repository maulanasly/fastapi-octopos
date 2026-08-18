"""Backfill product embeddings for semantic search.

Idempotent: re-embeds every product's name + description and updates the
row. Run after enabling embeddings on an existing catalog:

    python scripts/backfill_embeddings.py

Uses the app's configured EMBEDDING_PROVIDER (hash or api).
"""
import sys

sys.path.insert(0, ".")

from app.core.database import SessionLocal  # noqa: E402
from app.models.product import Product  # noqa: E402
from app.services.embeddings import embed_text  # noqa: E402


def main() -> int:
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        updated = skipped = 0
        for product in products:
            vector = embed_text(f"{product.name} {product.description or ''}")
            if vector is None:
                skipped += 1
                continue
            product.embedding = vector
            updated += 1
        db.commit()
        print(f"Embedded {updated} products ({skipped} skipped: no text / disabled)")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
