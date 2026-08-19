"""unique localization setting per tenant

Revision ID: 8e01c6e8a83c
Revises: 0015
Create Date: 2026-08-19 11:26:25.244263

The API relies on exactly one LocalizationSetting per tenant (first-row
semantics in app.core.localization). Enforce that at the database level:
deduplicate any existing rows (keep the lowest id per tenant), then add a
unique constraint. The plain tenant_id index becomes redundant once the
constraint exists, so it is dropped.

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8e01c6e8a83c"
down_revision: str | Sequence[str] | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "DELETE FROM localization_settings WHERE id NOT IN "
        "(SELECT MIN(id) FROM localization_settings GROUP BY tenant_id)"
    )
    op.drop_index(
        op.f("ix_localization_settings_tenant_id"), table_name="localization_settings"
    )
    op.create_unique_constraint(
        "uq_localization_settings_tenant_id", "localization_settings", ["tenant_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_localization_settings_tenant_id", "localization_settings", type_="unique"
    )
    op.create_index(
        op.f("ix_localization_settings_tenant_id"),
        "localization_settings",
        ["tenant_id"],
        unique=False,
    )
