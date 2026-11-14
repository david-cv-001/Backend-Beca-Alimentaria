"""create tenants table

Revision ID: 0002_create_tenants_table
Revises: 0001_enable_extensions
Create Date: 2026-11-14
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_create_tenants_table"
down_revision = "0001_enable_extensions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("folio", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("representative", sa.String(length=120), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("TRUE"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tenants"),
    )
    # Unicidad sin distinguir mayúsculas: la garantiza la base, no la aplicación.
    op.execute("CREATE UNIQUE INDEX uq_tenants_folio_ci ON tenants (lower(folio))")
    op.execute("CREATE UNIQUE INDEX uq_tenants_name_ci ON tenants (lower(name))")
    op.create_index("ix_tenants_active", "tenants", ["active"])


def downgrade() -> None:
    op.drop_index("ix_tenants_active", table_name="tenants")
    op.drop_table("tenants")
