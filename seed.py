"""Наполняет БД тестовыми данными (по одному пользователю каждой роли)."""
from datetime import date
from werkzeug.security import generate_password_hash
from app import create_app
from models import db, User, Organization, Kafedra, Teacher, Curator, Student, Task

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    # ── Организация ──────────────────────────────────────────────────────────
    org = Organization(
        name="ООО «Технологии будущего»",
        yur_adres="г. Москва, ул. Ленина, д. 1",
    )
    db.session.add(org)
    db.session.flush()

    # ── Кафедра ──────────────────────────────────────────────────────────────
    kafedra = Kafedra(
        name="Кафедра информационных систем",
        faculty="Факультет информатики и вычислительной техники",
    )
    db.session.add(kafedra)
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
        last_name="Иванов",
        first_name="Пётр",
        middle_name="Сергеевич",
        position="Доцент",
        email="ivanov@university.ru",
        kafedra_id=kafedra.id,
    )
    curator = Curator(
        user_id=curator_user.id,
        last_name="Смирнова",
        first_name="Анна",
        middle_name="Вячеславовна",
        position="Менеджер по персоналу",
        email="smirnova@techfuture.ru",
        organization_id=org.id,
    )
    db.session.add_all([teacher, curator])
    db.session.flush()

    student = Student(
        user_id=student_user.id,
        last_name="Петров",
        first_name="Алексей",
        middle_name="Николаевич",
        group_name="ИС-21",
        specialty="09.03.02 Информационные системы и технологии",
        email="petrov@student.university.ru",
        average_grade=4.50,
        kafedra_id=kafedra.id,
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
