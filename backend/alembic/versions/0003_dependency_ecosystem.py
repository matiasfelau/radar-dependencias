"""track dependency ecosystem

Revision ID: 0003_dependency_ecosystem
Revises: 0002_user_auth
Create Date: 2026-05-29 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003_dependency_ecosystem"
down_revision: str | None = "0002_user_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "dependencies",
        sa.Column("ecosystem", sa.String(length=16), nullable=False, server_default="pypi"),
    )
    op.execute(sa.text("UPDATE dependencies SET ecosystem = 'pypi' WHERE ecosystem IS NULL"))
    op.alter_column("dependencies", "ecosystem", server_default=None)


def downgrade() -> None:
    op.drop_column("dependencies", "ecosystem")