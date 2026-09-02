"""add product embedding ivfflat index

Revision ID: 0022
Revises: 0021
Create Date: 2026-09-02 23:10:00.000000

Sequential scan on vector <=> is slow at scale; add IVFFlat index.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0022"
down_revision: str | Sequence[str] | None = "0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("products"):
        return
    # Only for Postgres (pgvector); sqlite tests skip
    if bind.dialect.name != "postgresql":
        return
    # Check if index already exists
    indexes = inspector.get_indexes("products")
    if any(idx["name"] == "ix_products_embedding_ivfflat" for idx in indexes):
        return
    # ivfflat requires some rows for training; create anyway, will be usable after data
    # Use lists=100 for 5k-20k rows. CONCURRENTLY omitted for transactional alembic run;
    # in production consider CREATE INDEX CONCURRENTLY separately.
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_products_embedding_ivfflat "
            "ON products USING ivfflat (embedding vector_l2_ops) WITH (lists = 100)"
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(sa.text("DROP INDEX IF EXISTS ix_products_embedding_ivfflat"))
