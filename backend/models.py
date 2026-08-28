from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from sqlalchemy import func

class Base(DeclarativeBase):
    pass

class Project(Base):
    __tablename__ ="projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    description:Mapped[str | None] = mapped_column(
        nullable=True
    )
    status:Mapped[str] = mapped_column(
            default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now()
    )
    