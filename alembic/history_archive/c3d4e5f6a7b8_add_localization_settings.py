"""add_localization_settings

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-28 02:35:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("localization_settings"):
        op.create_table(
            "localization_settings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("language", sa.String(), nullable=False, server_default="en"),
            sa.Column("timezone", sa.String(), nullable=False, server_default="UTC"),
            sa.Column("currency", sa.String(), nullable=False, server_default="USD"),
            sa.Column(
                "date_format",
                sa.String(),
                nullable=False,
                server_default="%Y-%m-%d %H:%M:%S",
            ),
            sa.Column(
                "number_format", sa.String(), nullable=False, server_default="en_US"
            ),
            sa.Column("country_code", sa.String(), nullable=False, server_default="US"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_localization_settings_id"),
            "localization_settings",
            ["id"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("localization_settings"):
        op.drop_index(
            op.f("ix_localization_settings_id"), table_name="localization_settings"
        )
        op.drop_table("localization_settings")
