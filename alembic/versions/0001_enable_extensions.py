"""enable postgres extensions

Revision ID: 0001_enable_extensions
Revises:
Create Date: 2026-11-14
"""

from alembic import op

revision = "0001_enable_extensions"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pgcrypto aporta gen_random_uuid(); vector se deja listo para la fase de biometría.
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
