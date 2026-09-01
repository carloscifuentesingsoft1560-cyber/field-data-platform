from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from datetime import date
from sqlalchemy import ForeignKey, func, UniqueConstraint



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
    start_date : Mapped[date] = mapped_column(
        nullable=False
    )
    end_date: Mapped[date | None] = mapped_column(
         nullable=True   
    )

class Role(Base):
    __tablename__ ="roles"

    id:Mapped[int]= mapped_column(
        primary_key=True
    )
    name:Mapped[str]= mapped_column(
        unique=True,
        nullable=False
    )

class User(Base):
    __tablename__ ='users'
    id:Mapped[int] = mapped_column(
        primary_key=True
    )

    employee_number: Mapped[str] = mapped_column(
        unique=True,
        nullable=False
    )

    identification: Mapped[str] = mapped_column(
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        nullable=False
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey ("roles.id"),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )

class UserProject(Base):
    __tablename__="user_projects"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "project_id",
            name="uq_user_project"
        ),
    )

    id:Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    project_id:Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False
    )