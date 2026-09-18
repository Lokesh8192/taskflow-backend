from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class TaskHistory(Base):
    __tablename__ = "task_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey(
        "tasks.task_id",
        ondelete="CASCADE",
    ), nullable=False, index=True)
    changed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    old_priority: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_priority: Mapped[str | None] = mapped_column(String(20), nullable=True)
    old_assigned_to: Mapped[int | None] = mapped_column(nullable=True)
    new_assigned_to: Mapped[int | None] = mapped_column(nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(
        timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
