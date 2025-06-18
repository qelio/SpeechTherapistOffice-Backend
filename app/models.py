from typing import Optional

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, Date, Text, Integer, MetaData, Enum, Time
from datetime import datetime, date, time
from app.db import Base

class ActiveTest(Base):
    __tablename__ = "Active_tests"

    active_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    time_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    time_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(Enum('active_sent', 'active_not_sent', name='active_test_status'))
    assessment: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    test_id: Mapped[int] = mapped_column(ForeignKey("Tests.test_id"))
    lesson_id: Mapped[Optional[int]] = mapped_column(ForeignKey("Lessons.lesson_id"), nullable=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("Students.user_id"))
    teacher_id: Mapped[int] = mapped_column(ForeignKey("Teachers.user_id"))

    test: Mapped["Test"] = relationship()
    lesson: Mapped[Optional["Lesson"]] = relationship()
    student: Mapped["Student"] = relationship()
    teacher: Mapped["Teacher"] = relationship()
    packages: Mapped[list["TestPackage"]] = relationship(back_populates="active_test")


class TestPackage(Base):
    __tablename__ = "Tests_packages"

    package_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    status_verification: Mapped[str] = mapped_column(Enum('verified', 'not_verified', name='verification_status'))
    exercise_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    exercise_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    student_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    accumulated_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    active_id: Mapped[int] = mapped_column(ForeignKey("Active_tests.active_id"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("Education_exerсizes.exercise_id"))

    active_test: Mapped["ActiveTest"] = relationship(back_populates="packages")
    exercise: Mapped["EducationExercise"] = relationship()

class Test(Base):
    __tablename__ = "Tests"

    test_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    complexity: Mapped[str] = mapped_column(Enum('easy', 'medium', 'difficult', name='complexity_enum'))

    discipline_id: Mapped[int] = mapped_column(ForeignKey("Disciplines.discipline_id"))
    teacher_id: Mapped[int] = mapped_column(ForeignKey("Teachers.user_id"))

    discipline: Mapped["Discipline"] = relationship()
    teacher: Mapped["Teacher"] = relationship()
    exercise_associations: Mapped[list["TestExerciseAssociation"]] = relationship(
        back_populates="test"
    )
    exercises: Mapped[list["EducationExercise"]] = relationship(
        secondary="Tests_has_Education_exerсizes",
        viewonly=True
    )


class TestExerciseAssociation(Base):
    __tablename__ = "Tests_has_Education_exerсizes"

    test_id: Mapped[int] = mapped_column(
        ForeignKey("Tests.test_id"),
        primary_key=True
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("Education_exerсizes.exercise_id"),
        primary_key=True
    )
    purpose_at: Mapped[datetime] = mapped_column(DateTime)

    test: Mapped["Test"] = relationship(back_populates="exercise_associations")
    exercise: Mapped["EducationExercise"] = relationship(back_populates="test_associations")

class EducationClassifier(Base):
    __tablename__ = "Education_classifier"

    classifier_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    administrator_id: Mapped[int] = mapped_column(ForeignKey("Administrators.Users_user_id"))
    discipline_id: Mapped[int] = mapped_column(ForeignKey("Disciplines.discipline_id"))

    administrator: Mapped["Administrator"] = relationship()
    discipline: Mapped["Discipline"] = relationship()
    modules: Mapped[list["EducationModule"]] = relationship(back_populates="classifier")


class EducationModule(Base):
    __tablename__ = "Education_modules"

    module_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(Text)
    preview_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    classifier_id: Mapped[int] = mapped_column(ForeignKey("Education_classifier.classifier_id"))
    teacher_id: Mapped[int] = mapped_column(ForeignKey("Teachers.user_id"))

    classifier: Mapped["EducationClassifier"] = relationship(back_populates="modules")
    teacher: Mapped["Teacher"] = relationship()
    exercises: Mapped[list["EducationExercise"]] = relationship(back_populates="module")


class EducationExercise(Base):
    __tablename__ = "Education_exerсizes"

    exercise_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    verification_type: Mapped[str] = mapped_column(Enum('auto', 'manual', name='verification_type_enum'))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    right_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_score: Mapped[int] = mapped_column(Integer)

    module_id: Mapped[int] = mapped_column(ForeignKey("Education_modules.module_id"))
    teacher_id: Mapped[int] = mapped_column(ForeignKey("Teachers.user_id"))

    module: Mapped["EducationModule"] = relationship(back_populates="exercises")
    teacher: Mapped["Teacher"] = relationship()
    test_associations: Mapped[list["TestExerciseAssociation"]] = relationship(
        back_populates="exercise"
    )
    tests: Mapped[list["Test"]] = relationship(
        secondary="Tests_has_Education_exerсizes",
        viewonly=True
    )
    test_packages: Mapped[list["TestPackage"]] = relationship(back_populates="exercise")


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
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="classroom")

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
    duration: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(
        Enum('scheduled', 'completed', 'cancelled_in_time', 'missed', name='lesson_status'))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    online_call_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    subscription_id: Mapped[int | None] = mapped_column(
        ForeignKey("Subscriptions.subscription_id"),
        nullable=True
    )
    classroom_id: Mapped[int | None] = mapped_column(
        ForeignKey("Classrooms.classroom_id"),
        nullable=True
    )
    discipline_id: Mapped[int | None] = mapped_column(
        ForeignKey("Disciplines.discipline_id"),
        nullable=True
    )

    teacher_id: Mapped[int] = mapped_column(ForeignKey("Teachers.user_id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("Students.user_id"))

    subscription: Mapped["Subscription"] = relationship(back_populates="lessons")
    teacher: Mapped["Teacher"] = relationship()
    student: Mapped["Student"] = relationship()
    classroom: Mapped["Classroom"] = relationship(back_populates="lessons")
    discipline: Mapped["Discipline"] = relationship()

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

