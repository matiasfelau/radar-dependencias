from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Dependency(Base):
    __tablename__ = "dependencies"
    __table_args__ = (
        UniqueConstraint("environment_id", "package_name", name="uq_dependency_environment_package"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    environment_id: Mapped[int] = mapped_column(
        ForeignKey("environments.id", ondelete="CASCADE"), nullable=False
    )
    package_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    installed_version: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    environment: Mapped["Environment"] = relationship(back_populates="dependencies")
