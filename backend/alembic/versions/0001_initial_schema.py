"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-16 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


severity_level = sa.Enum(
    "Low",
    "Medium",
    "High",
    "Critical",
    "Unknown",
    name="severity_level",
    native_enum=False,
)
vulnerability_status = sa.Enum(
    "Active",
    "Resolved",
    name="vulnerability_status",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("api_key", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("api_key"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_projects_id"), "projects", ["id"], unique=False)
    op.create_index(op.f("ix_projects_name"), "projects", ["name"], unique=False)

    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name="uq_setting_key"),
    )
    op.create_index(op.f("ix_settings_id"), "settings", ["id"], unique=False)

    op.create_table(
        "vulnerabilities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cve_id", sa.String(length=64), nullable=False),
        sa.Column("package_name", sa.String(length=255), nullable=False),
        sa.Column("affected_version", sa.String(length=128), nullable=False),
        sa.Column("severity", severity_level, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("has_exploit", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("exploit_url", sa.String(length=512), nullable=True),
        sa.Column("status", vulnerability_status, nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "cve_id",
            "package_name",
            "affected_version",
            name="uq_vulnerability_cve_package_version",
        ),
    )
    op.create_index(op.f("ix_vulnerabilities_affected_version"), "vulnerabilities", ["affected_version"], unique=False)
    op.create_index(op.f("ix_vulnerabilities_cve_id"), "vulnerabilities", ["cve_id"], unique=False)
    op.create_index(op.f("ix_vulnerabilities_id"), "vulnerabilities", ["id"], unique=False)
    op.create_index(op.f("ix_vulnerabilities_package_name"), "vulnerabilities", ["package_name"], unique=False)
    op.create_index(op.f("ix_vulnerabilities_status"), "vulnerabilities", ["status"], unique=False)

    op.create_table(
        "environments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "name", name="uq_environment_project_name"),
    )
    op.create_index(op.f("ix_environments_id"), "environments", ["id"], unique=False)

    op.create_table(
        "dependencies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("environment_id", sa.Integer(), nullable=False),
        sa.Column("package_name", sa.String(length=255), nullable=False),
        sa.Column("installed_version", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(["environment_id"], ["environments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("environment_id", "package_name", name="uq_dependency_environment_package"),
    )
    op.create_index(op.f("ix_dependencies_id"), "dependencies", ["id"], unique=False)
    op.create_index(op.f("ix_dependencies_installed_version"), "dependencies", ["installed_version"], unique=False)
    op.create_index(op.f("ix_dependencies_package_name"), "dependencies", ["package_name"], unique=False)

    op.execute(
        sa.text(
            """
            INSERT INTO settings (key, value)
            VALUES ('scan_interval_seconds', '43200')
            ON CONFLICT (key) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_dependencies_package_name"), table_name="dependencies")
    op.drop_index(op.f("ix_dependencies_installed_version"), table_name="dependencies")
    op.drop_index(op.f("ix_dependencies_id"), table_name="dependencies")
    op.drop_table("dependencies")

    op.drop_index(op.f("ix_environments_id"), table_name="environments")
    op.drop_table("environments")

    op.drop_index(op.f("ix_vulnerabilities_status"), table_name="vulnerabilities")
    op.drop_index(op.f("ix_vulnerabilities_package_name"), table_name="vulnerabilities")
    op.drop_index(op.f("ix_vulnerabilities_id"), table_name="vulnerabilities")
    op.drop_index(op.f("ix_vulnerabilities_cve_id"), table_name="vulnerabilities")
    op.drop_index(op.f("ix_vulnerabilities_affected_version"), table_name="vulnerabilities")
    op.drop_table("vulnerabilities")

    op.drop_index(op.f("ix_settings_id"), table_name="settings")
    op.drop_table("settings")

    op.drop_index(op.f("ix_projects_name"), table_name="projects")
    op.drop_index(op.f("ix_projects_id"), table_name="projects")
    op.drop_table("projects")

    severity_level.drop(op.get_bind(), checkfirst=True)
    vulnerability_status.drop(op.get_bind(), checkfirst=True)
