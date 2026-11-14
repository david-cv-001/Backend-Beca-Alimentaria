"""create users table

Revision ID: 0003_create_users_table
Revises: 0002_create_tenants_table
Create Date: 2026-11-14
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_create_users_table"
down_revision = "0002_create_tenants_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("username", sa.String(length=30), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=15), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("TRUE"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_users_tenant_id",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("role IN ('SUPERADMIN', 'ADMIN', 'CHECKER')", name="ck_users_role"),
        sa.CheckConstraint(
            "(role = 'SUPERADMIN' AND tenant_id IS NULL) "
            "OR (role IN ('ADMIN', 'CHECKER') AND tenant_id IS NOT NULL)",
            name="ck_users_tenant_by_role",
        ),
    )
    op.execute("CREATE UNIQUE INDEX uq_users_username_ci ON users (lower(username))")
    op.execute("CREATE UNIQUE INDEX uq_users_email_ci ON users (lower(email))")
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_active", "users", ["active"])


def downgrade() -> None:
    op.drop_index("ix_users_active", table_name="users")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_table("users")
