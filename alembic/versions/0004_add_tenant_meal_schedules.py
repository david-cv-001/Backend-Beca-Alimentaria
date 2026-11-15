"""add tenant meal schedules

Revision ID: 0004_add_tenant_meal_schedules
Revises: 0003_create_users_table
Create Date: 2026-11-15
"""

import sqlalchemy as sa

from alembic import op

revision = "0004_add_tenant_meal_schedules"
down_revision = "0003_create_users_table"
branch_labels = None
depends_on = None

# Valores por defecto de las ventanas de servicio (hora local de la cafetería).
BREAKFAST_START = "'07:00'"
BREAKFAST_END = "'10:00'"
LUNCH_START = "'13:00'"
LUNCH_END = "'16:00'"


def upgrade() -> None:
    # 1) Se agregan nullable para poder rellenar las cafeterías ya existentes.
    op.add_column("tenants", sa.Column("breakfast_start", sa.Time(), nullable=True))
    op.add_column("tenants", sa.Column("breakfast_end", sa.Time(), nullable=True))
    op.add_column("tenants", sa.Column("lunch_start", sa.Time(), nullable=True))
    op.add_column("tenants", sa.Column("lunch_end", sa.Time(), nullable=True))

    # 2) Backfill de las filas existentes con los valores por defecto.
    op.execute(
        "UPDATE tenants SET "
        f"breakfast_start = {BREAKFAST_START}, breakfast_end = {BREAKFAST_END}, "
        f"lunch_start = {LUNCH_START}, lunch_end = {LUNCH_END} "
        "WHERE breakfast_start IS NULL"
    )

    # 3) Ahora sí, obligatorias y con default para inserciones fuera de la API.
    op.alter_column(
        "tenants",
        "breakfast_start",
        nullable=False,
        server_default=sa.text(BREAKFAST_START),
    )
    op.alter_column(
        "tenants",
        "breakfast_end",
        nullable=False,
        server_default=sa.text(BREAKFAST_END),
    )
    op.alter_column(
        "tenants",
        "lunch_start",
        nullable=False,
        server_default=sa.text(LUNCH_START),
    )
    op.alter_column(
        "tenants",
        "lunch_end",
        nullable=False,
        server_default=sa.text(LUNCH_END),
    )


def downgrade() -> None:
    op.drop_column("tenants", "lunch_end")
    op.drop_column("tenants", "lunch_start")
    op.drop_column("tenants", "breakfast_end")
    op.drop_column("tenants", "breakfast_start")
