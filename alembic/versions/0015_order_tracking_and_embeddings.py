"""order_tracking_and_embeddings

Revision ID: 0015
Revises: 0014
Create Date: 2026-08-18 12:55:00.000000

Adds the generic order-tracking layer plus semantic search support:

* ``orders`` gain an optional destination (address + lat/lng + native
  ``point``) and a forward-only ``tracking_status`` (``none`` ->
  ``assigned`` -> ``en_route`` -> ``on_site``) with stage timestamps,
  mirroring the serving machine. A GiST ``point_ops`` index on
  ``destination`` powers nearest-neighbor queries.
* New ``order_location_updates`` table: append-only ping history
  (lat/lng + native ``point``, source, timestamp) with a GiST index for
  radius / KNN lookups.
* ``products`` gain a ``vector(384)`` ``embedding`` column with an HNSW
  cosine index for semantic catalog search (pgvector).
* Extensions: ``vector``, ``cube`` and ``earthdistance`` (great-circle
  radius queries) are created if absent. ``earthdistance`` requires
  ``cube``. Portable across PostgreSQL only; the tracking feature is
  Postgres-exclusive (native ``point`` type + pgvector).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0015"
down_revision: str | Sequence[str] | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("orders"):
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS cube")
    op.execute("CREATE EXTENSION IF NOT EXISTS earthdistance")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # --- orders: destination + tracking state machine ---
    orders_existing = {c["name"] for c in inspector.get_columns("orders")}
    order_columns = [
        sa.Column("destination_address", sa.Text(), nullable=True),
        sa.Column("destination_lat", sa.Float(), nullable=True),
        sa.Column("destination_lng", sa.Float(), nullable=True),
        sa.Column(
            "tracking_status",
            sa.String(),
            nullable=False,
            server_default="none",
        ),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("en_route_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("on_site_at", sa.DateTime(timezone=True), nullable=True),
    ]
    for col in order_columns:
        if col.name not in orders_existing:
            op.add_column("orders", col)
    if "destination" not in orders_existing:
        op.execute("ALTER TABLE orders ADD COLUMN destination point")
    op.create_index(
        "ix_orders_tracking_status",
        "orders",
        ["tracking_status"],
    )
    if "destination" in orders_existing:
        pass
    else:
        op.execute(
            """
            CREATE INDEX ix_orders_destination_gist
            ON orders USING gist (destination)
            """
        )

    # --- order_location_updates: append-only ping history ---
    if not inspector.has_table("order_location_updates"):
        op.create_table(
            "order_location_updates",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column(
                "tenant_id",
                sa.Integer(),
                sa.ForeignKey("tenants.id"),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "order_id",
                sa.Integer(),
                sa.ForeignKey("orders.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("lat", sa.Float(), nullable=False),
            sa.Column("lng", sa.Float(), nullable=False),
            sa.Column(
                "source",
                sa.String(),
                nullable=False,
                server_default="gps",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
            ),
        )
        op.execute("ALTER TABLE order_location_updates ADD COLUMN location point")
        op.execute(
            """
            CREATE INDEX ix_order_location_updates_location_gist
            ON order_location_updates USING gist (location)
            """
        )

    # --- products: semantic search embedding ---
    if inspector.has_table("products"):
        products_existing = {c["name"] for c in inspector.get_columns("products")}
        if "embedding" not in products_existing:
            op.execute("ALTER TABLE products ADD COLUMN embedding vector(384)")
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_products_embedding_hnsw
            ON products USING hnsw (embedding vector_cosine_ops)
            """
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("orders"):
        return

    op.execute("DROP INDEX IF EXISTS ix_orders_destination_gist")
    op.execute("DROP INDEX IF EXISTS ix_order_location_updates_location_gist")
    op.execute("DROP INDEX IF EXISTS ix_products_embedding_hnsw")
    op.drop_index("ix_orders_tracking_status", table_name="orders")
    for name in (
        "destination_address",
        "destination_lat",
        "destination_lng",
        "destination",
        "tracking_status",
        "assigned_at",
        "en_route_at",
        "on_site_at",
    ):
        if name in {c["name"] for c in inspector.get_columns("orders")}:
            op.drop_column("orders", name)
    if inspector.has_table("order_location_updates"):
        op.drop_table("order_location_updates")
    if inspector.has_table("products"):
        columns = {c["name"] for c in inspector.get_columns("products")}
        if "embedding" in columns:
            op.drop_column("products", "embedding")
