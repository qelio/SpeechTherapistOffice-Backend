from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, Date, Text, Integer, MetaData, Enum
from datetime import datetime, date
from app.db import Base

class User(Base):
    __tablename__ = "Users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    birthday: Mapped[date] = mapped_column(Date)
    gender: Mapped[str] = mapped_column(Enum("Male", "Female", name="gender_enum"))
    city: Mapped[str] = mapped_column(String(50))
    phone_number: Mapped[str] = mapped_column(String(20))
    profile_picture_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unique_code: Mapped[str] = mapped_column(String(255), unique=True)

    student: Mapped["Student"] = relationship(back_populates="user", uselist=False)
    teacher: Mapped["Teacher"] = relationship(back_populates="user", uselist=False)
    parent: Mapped["Parent"] = relationship(back_populates="user", uselist=False)
    administrator: Mapped["Administrator"] = relationship(back_populates="user", uselist=False)

class Student(Base):
    __tablename__ = "Students"

    user_id: Mapped[int] = mapped_column(ForeignKey("Users.user_id"), primary_key=True)
    class_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    school_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    user: Mapped["User"] = relationship(back_populates="student")

class Teacher(Base):
    __tablename__ = "Teachers"

    user_id: Mapped[int] = mapped_column(ForeignKey("Users.user_id"), primary_key=True)
    experience: Mapped[int] = mapped_column(Integer)
    main_work: Mapped[str] = mapped_column(String(100))

    user: Mapped["User"] = relationship(back_populates="teacher")

class Parent(Base):
    __tablename__ = "Parents"

    user_id: Mapped[int] = mapped_column(ForeignKey("Users.user_id"), primary_key=True)
    work_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    work_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    user: Mapped["User"] = relationship(back_populates="parent")

class Administrator(Base):
    __tablename__ = "Administrators"

    Users_user_id: Mapped[int] = mapped_column(ForeignKey("Users.user_id"), primary_key=True)
    access_level: Mapped[str | None] = mapped_column(Enum("logs", "full", name="access_level_enum"), nullable=True)

    user: Mapped["User"] = relationship(back_populates="administrator")


