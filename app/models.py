from typing import Optional

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, Date, Text, Integer, MetaData, Enum, Time
from datetime import datetime, date, time
from app.db import Base


class Branch(Base):
    __tablename__ = "Branches"

    branch_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    address: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    working_start: Mapped[time] = mapped_column(Time)
    working_end: Mapped[time] = mapped_column(Time)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    administrator_id: Mapped[int] = mapped_column(ForeignKey("Administrators.Users_user_id"))

    administrator: Mapped["Administrator"] = relationship(back_populates="branches")
    classrooms: Mapped[list["Classroom"]] = relationship(back_populates="branch")

class Classroom(Base):
    __tablename__ = "Classrooms"

    classroom_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(10))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    branch_id: Mapped[int] = mapped_column(ForeignKey("Branches.branch_id"))
    administrator_id: Mapped[int] = mapped_column(ForeignKey("Administrators.Users_user_id"))

    branch: Mapped["Branch"] = relationship(back_populates="classrooms")
    administrator: Mapped["Administrator"] = relationship(back_populates="classrooms")

class Discipline(Base):
    __tablename__ = "Disciplines"

    discipline_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    administrator_id: Mapped[int] = mapped_column(ForeignKey("Administrators.Users_user_id"))

    administrator: Mapped["Administrator"] = relationship(back_populates="disciplines")
    teacher_associations: Mapped[list["TeacherDisciplineAssociation"]] = relationship(
        back_populates="discipline"
    )
    teachers: Mapped[list["Teacher"]] = relationship(
        secondary="Teachers_has_Disciplines",
        back_populates="disciplines",
        viewonly=True
    )

class TeacherDisciplineAssociation(Base):
    __tablename__ = "Teachers_has_Disciplines"

    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("Teachers.user_id"),
        primary_key=True
    )
    discipline_id: Mapped[int] = mapped_column(
        ForeignKey("Disciplines.discipline_id"),
        primary_key=True
    )

    teacher: Mapped["Teacher"] = relationship(back_populates="discipline_associations")
    discipline: Mapped["Discipline"] = relationship(back_populates="teacher_associations")



class Subscription(Base):
    __tablename__ = "Subscriptions"

    subscription_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    total_lessons: Mapped[int] = mapped_column()
    start_date: Mapped[date] = mapped_column()
    end_date: Mapped[date] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    in_archive: Mapped[bool] = mapped_column(default=False)

    student_id: Mapped[int] = mapped_column(ForeignKey("Students.user_id"))
    teacher_id: Mapped[int] = mapped_column(ForeignKey("Teachers.user_id"))

    student: Mapped["Student"] = relationship(back_populates="subscriptions")
    teacher: Mapped["Teacher"] = relationship(back_populates="subscriptions")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="subscription")


class Lesson(Base):
    __tablename__ = "Lessons"

    lesson_id: Mapped[int] = mapped_column(primary_key=True)
    lesson_date_time: Mapped[datetime] = mapped_column()
    duration: Mapped[int] = mapped_column()  # продолжительность в минутах
    status: Mapped[str] = mapped_column(
        Enum('scheduled', 'completed', 'cancelled_in_time', 'missed', name='lesson_status'))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    online_call_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    subscription_id: Mapped[int | None] = mapped_column(
        ForeignKey("Subscriptions.subscription_id"),
        nullable=True
    )
    teacher_id: Mapped[int] = mapped_column(ForeignKey("Teachers.user_id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("Students.user_id"))

    subscription: Mapped["Subscription"] = relationship(back_populates="lessons")
    teacher: Mapped["Teacher"] = relationship()
    student: Mapped["Student"] = relationship()


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

class StudentTeacherAssociation(Base):
    __tablename__ = "Students_has_Teachers"

    student_user_id: Mapped[int] = mapped_column(
        ForeignKey("Students.user_id"),
        primary_key=True
    )
    teacher_user_id: Mapped[int] = mapped_column(
        ForeignKey("Teachers.user_id"),
        primary_key=True
    )

    student: Mapped["Student"] = relationship(backref="teacher_associations")
    teacher: Mapped["Teacher"] = relationship(backref="student_associations")

class Student(Base):
    __tablename__ = "Students"

    user_id: Mapped[int] = mapped_column(ForeignKey("Users.user_id"), primary_key=True)
    class_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    school_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    user: Mapped["User"] = relationship(back_populates="student")
    teachers: Mapped[list["Teacher"]] = relationship(
        secondary="Students_has_Teachers",
        viewonly=True,
        overlaps="teacher_associations"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="student")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="student")

class Teacher(Base):
    __tablename__ = "Teachers"

    user_id: Mapped[int] = mapped_column(ForeignKey("Users.user_id"), primary_key=True)
    experience: Mapped[int] = mapped_column(Integer)
    main_work: Mapped[str] = mapped_column(String(100))

    user: Mapped["User"] = relationship(back_populates="teacher")
    students: Mapped[list["Student"]] = relationship(
        secondary="Students_has_Teachers",
        viewonly=True,
        overlaps="student_associations"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="teacher")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="teacher")
    discipline_associations: Mapped[list["TeacherDisciplineAssociation"]] = relationship(
        back_populates="teacher"
    )
    disciplines: Mapped[list["Discipline"]] = relationship(
        secondary="Teachers_has_Disciplines",
        back_populates="teachers",
        viewonly=True
    )

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
    disciplines: Mapped[list["Discipline"]] = relationship(back_populates="administrator")
    branches: Mapped[list["Branch"]] = relationship(back_populates="administrator")
    classrooms: Mapped[list["Classroom"]] = relationship(back_populates="administrator")

