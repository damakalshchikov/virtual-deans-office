"""Наполняет БД тестовыми данными (по одному пользователю каждой роли)."""
from datetime import date
from werkzeug.security import generate_password_hash
from app import create_app
from models import db, User, Organization, Teacher, Curator, Student, Task

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    # ── Организация ──────────────────────────────────────────────────────────
    org = Organization(name="ООО «Технологии будущего»")
    db.session.add(org)
    db.session.flush()

    # ── Пользователи ─────────────────────────────────────────────────────────
    admin_user   = User(login="admin",   password=generate_password_hash("admin123"),   role="admin")
    teacher_user = User(login="teacher", password=generate_password_hash("teacher123"), role="teacher")
    curator_user = User(login="curator", password=generate_password_hash("curator123"), role="curator")
    student_user = User(login="student", password=generate_password_hash("student123"), role="student")

    db.session.add_all([admin_user, teacher_user, curator_user, student_user])
    db.session.flush()

    # ── Профили ──────────────────────────────────────────────────────────────
    teacher = Teacher(
        user_id=teacher_user.id,
        full_name="Иванов Пётр Сергеевич",
        department="Кафедра информационных систем",
    )
    curator = Curator(
        user_id=curator_user.id,
        full_name="Смирнова Анна Вячеславовна",
        organization_id=org.id,
    )
    db.session.add_all([teacher, curator])
    db.session.flush()

    student = Student(
        user_id=student_user.id,
        full_name="Петров Алексей Николаевич",
        group_name="ИС-21",
        specialty="09.03.02 Информационные системы и технологии",
        internship_start=date(2026, 2, 3),
        internship_end=date(2026, 3, 28),
        organization_id=org.id,
        teacher_id=teacher.id,
        curator_id=curator.id,
    )
    db.session.add(student)
    db.session.flush()

    tasks = [
        Task(student_id=student.id, title="Изучить стек технологий организации", status="done"),
        Task(student_id=student.id, title="Разработать модуль отчётности",        status="pending"),
        Task(student_id=student.id, title="Написать отчёт о практике",            status="pending"),
    ]
    db.session.add_all(tasks)
    db.session.commit()

    print("Тестовые данные добавлены.")
    print()
    print("Учётные записи:")
    print("  admin   / admin123   — Администратор")
    print("  teacher / teacher123 — Преподаватель")
    print("  curator / curator123 — Куратор")
    print("  student / student123 — Студент")
