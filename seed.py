"""Наполняет БД тестовыми данными."""
from datetime import date
from werkzeug.security import generate_password_hash
from app import create_app
from models import (db, User, Organization, Kafedra, Teacher, Curator, Student,
                     Task, Permission, RolePermission, Kompetenciya, StudentKompetenciya,
                     Practice, PracticeStage, Vacancy, VacancyRequirement,
                     Application, Commission, Notification)

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    # ── Организации ──
    orgs = [
        Organization(name="ООО «Технологии будущего»", yur_adres="г. Москва, ул. Ленина, д. 1"),
        Organization(name="ПАО «Цифровые решения»", yur_adres="г. Москва, ул. Кутузова, д. 15"),
        Organization(name="АО «Инновационные системы»", yur_adres="г. Москва, пр. Мира, д. 42"),
    ]
    db.session.add_all(orgs)
    db.session.flush()

    # ── Кафедры ──
    kafedras = [
        Kafedra(name="Управления и информатики в технических системах", faculty="Институт информационных технологий"),
        Kafedra(name="Прикладной математики", faculty="Факультет информатики"),
    ]
    db.session.add_all(kafedras)
    db.session.flush()

    # ── Компетенции ──
    komp_names = ["Python", "SQL", "JavaScript", "HTML/CSS", "Git", "REST API",
                   "Машинное обучение", "Базы данных", "Linux", "Docker"]
    komps = [Kompetenciya(name=n) for n in komp_names]
    db.session.add_all(komps)
    db.session.flush()

    # ── Пользователи ──
    admin_u   = User(login="admin",    password=generate_password_hash("admin123"),    role="admin")
    teacher_u = User(login="teacher",  password=generate_password_hash("teacher123"),  role="teacher")
    teacher2_u = User(login="teacher2", password=generate_password_hash("teacher123"), role="teacher")
    curator_u = User(login="curator",  password=generate_password_hash("curator123"),  role="curator")
    stud1_u   = User(login="student",  password=generate_password_hash("student123"),  role="student")
    stud2_u   = User(login="student2", password=generate_password_hash("student123"),  role="student")
    stud3_u   = User(login="student3", password=generate_password_hash("student123"),  role="student")
    stud4_u   = User(login="student4", password=generate_password_hash("student123"),  role="student")
    db.session.add_all([admin_u, teacher_u, teacher2_u, curator_u, stud1_u, stud2_u, stud3_u, stud4_u])
    db.session.flush()

    # ── Профили ──
    t1 = Teacher(user_id=teacher_u.id, last_name="Бычков", first_name="Сергей",
                 middle_name="Юрьевич", position="Доцент", email="bychkov@stankin.ru", kafedra_id=kafedras[0].id)
    t2 = Teacher(user_id=teacher2_u.id, last_name="Иванов", first_name="Пётр",
                 middle_name="Сергеевич", position="Профессор", email="ivanov@stankin.ru", kafedra_id=kafedras[1].id)
    c1 = Curator(user_id=curator_u.id, last_name="Смирнова", first_name="Анна",
                 middle_name="Вячеславовна", position="Менеджер", email="smirnova@techfuture.ru", organization_id=orgs[0].id)
    db.session.add_all([t1, t2, c1])
    db.session.flush()

    s1 = Student(user_id=stud1_u.id, last_name="Кутенков", first_name="Сергей", middle_name="Дмитриевич",
                 group_name="ИДБ-23-14", specialty="09.03.03 Прикладная информатика",
                 email="kutenkov@student.stankin.ru", average_grade=4.50,
                 kafedra_id=kafedras[0].id, internship_start=date(2026, 2, 3), internship_end=date(2026, 3, 28),
                 organization_id=orgs[0].id, teacher_id=t1.id, curator_id=c1.id)
    s2 = Student(user_id=stud2_u.id, last_name="Эрендженова", first_name="Мария", middle_name="Николаевна",
                 group_name="ИДБ-23-14", specialty="09.03.03 Прикладная информатика",
                 email="erendzhenova@student.stankin.ru", average_grade=4.80,
                 kafedra_id=kafedras[0].id, teacher_id=t1.id, curator_id=c1.id)
    s3 = Student(user_id=stud3_u.id, last_name="Дамакальщиков", first_name="Михаил", middle_name="Александрович",
                 group_name="ИДБ-23-14", specialty="09.03.03 Прикладная информатика",
                 email="damakalshikov@student.stankin.ru", average_grade=4.20,
                 kafedra_id=kafedras[0].id, teacher_id=t1.id)
    s4 = Student(user_id=stud4_u.id, last_name="Осипов", first_name="Илья", middle_name="Александрович",
                 group_name="ИДБ-23-14", specialty="09.03.03 Прикладная информатика",
                 email="osipov@student.stankin.ru", average_grade=4.20,
                 kafedra_id=kafedras[0].id, teacher_id=t1.id)
    db.session.add_all([s1, s2, s3, s4])
    db.session.flush()

    # ── Компетенции студентов ──
    student_komps = [
        (s1.id, komps[0].id, 4), (s1.id, komps[1].id, 3), (s1.id, komps[2].id, 3),
        (s1.id, komps[4].id, 4), (s1.id, komps[5].id, 2), (s1.id, komps[7].id, 3),
        (s2.id, komps[0].id, 5), (s2.id, komps[1].id, 4), (s2.id, komps[3].id, 5),
        (s2.id, komps[4].id, 4), (s2.id, komps[6].id, 3), (s2.id, komps[8].id, 3),
        (s3.id, komps[0].id, 3), (s3.id, komps[1].id, 2), (s3.id, komps[2].id, 4),
        (s3.id, komps[3].id, 4), (s3.id, komps[9].id, 2), (s4.id, komps[0].id, 3),
        (s4.id, komps[1].id, 2), (s4.id, komps[2].id, 4),
    ]
    for sid, kid, lvl in student_komps:
        db.session.add(StudentKompetenciya(student_id=sid, kompetenciya_id=kid, level=lvl))

    # ── Практики ──
    pr1 = Practice(name="Производственная практика 2026", type="Производственная",
                    start_date=date(2026, 2, 3), end_date=date(2026, 3, 28),
                    status="active", teacher_id=t1.id,
                    description="Производственная практика для студентов 3 курса направления «Прикладная информатика»")
    pr2 = Practice(name="Преддипломная практика 2026", type="Преддипломная",
                    start_date=date(2026, 9, 1), end_date=date(2026, 10, 31),
                    status="planned", teacher_id=t1.id)
    db.session.add_all([pr1, pr2])
    db.session.flush()

    # ── Этапы ──
    stages = [
        PracticeStage(practice_id=pr1.id, name="Ознакомление с организацией", start_date=date(2026, 2, 3), end_date=date(2026, 2, 14), order=1),
        PracticeStage(practice_id=pr1.id, name="Выполнение индивидуального задания", start_date=date(2026, 2, 17), end_date=date(2026, 3, 14), order=2),
        PracticeStage(practice_id=pr1.id, name="Подготовка отчётной документации", start_date=date(2026, 3, 17), end_date=date(2026, 3, 28), order=3),
    ]
    db.session.add_all(stages)

    # ── Вакансии ──
    v1 = Vacancy(title="Стажёр-разработчик Python", description="Backend разработка на Python/Django",
                  slots=2, organization_id=orgs[0].id, practice_id=pr1.id)
    v2 = Vacancy(title="Frontend-разработчик", description="Разработка интерфейсов на React",
                  slots=1, organization_id=orgs[1].id, practice_id=pr1.id)
    v3 = Vacancy(title="Data Analyst", description="Анализ данных и ML",
                  slots=1, organization_id=orgs[2].id, practice_id=pr1.id)
    db.session.add_all([v1, v2, v3])
    db.session.flush()

    # ── Требования вакансий ──
    vr = [
        VacancyRequirement(vacancy_id=v1.id, kompetenciya_id=komps[0].id, min_level=3),
        VacancyRequirement(vacancy_id=v1.id, kompetenciya_id=komps[1].id, min_level=2),
        VacancyRequirement(vacancy_id=v1.id, kompetenciya_id=komps[5].id, min_level=2),
        VacancyRequirement(vacancy_id=v2.id, kompetenciya_id=komps[2].id, min_level=3),
        VacancyRequirement(vacancy_id=v2.id, kompetenciya_id=komps[3].id, min_level=3),
        VacancyRequirement(vacancy_id=v3.id, kompetenciya_id=komps[0].id, min_level=3),
        VacancyRequirement(vacancy_id=v3.id, kompetenciya_id=komps[6].id, min_level=2),
    ]
    db.session.add_all(vr)

    # ── Задания ──
    tasks = [
        Task(student_id=s1.id, practice_id=pr1.id, title="Изучить стек технологий организации",
             status="accepted", due_date=date(2026, 2, 14)),
        Task(student_id=s1.id, practice_id=pr1.id, title="Разработать модуль авторизации",
             status="in_progress", due_date=date(2026, 3, 7)),
        Task(student_id=s1.id, practice_id=pr1.id, title="Написать отчёт о практике",
             status="pending", due_date=date(2026, 3, 28)),
        Task(student_id=s2.id, practice_id=pr1.id, title="Разработать интерфейс планирования",
             status="submitted", due_date=date(2026, 3, 14)),
    ]
    db.session.add_all(tasks)

    # ── Комиссия ──
    comm = Commission(name="Аттестационная комиссия ИДБ-23",
                       chairman="Бычков С.Ю.", session_date=date(2026, 4, 10),
                       kafedra_id=kafedras[0].id)
    db.session.add(comm)

    # ── Права доступа ──
    PERMISSIONS = [
        ("view_practices", "Просмотр списка практик", "Организация и планирование практики"),
        ("create_practice", "Создание практики", "Организация и планирование практики"),
        ("edit_practice", "Редактирование практики", "Организация и планирование практики"),
        ("view_vacancies", "Просмотр вакансий", "Распределение студентов"),
        ("manage_vacancies", "Управление вакансиями", "Распределение студентов"),
        ("view_own_tasks", "Просмотр своих заданий", "Задания и выполнение"),
        ("complete_task", "Отмечать задания выполненными", "Задания и выполнение"),
        ("view_all_tasks", "Просмотр всех заданий", "Задания и выполнение"),
        ("view_reports", "Просмотр отчётов", "Аттестация"),
        ("export_reports", "Экспорт отчётов", "Аттестация"),
        ("manage_users", "Управление пользователями", "Администрирование"),
        ("manage_roles", "Управление ролями", "Администрирование"),
        ("manage_permissions", "Управление правами", "Администрирование"),
    ]

    ROLE_DEFAULTS = {
        "student": {"view_practices", "view_vacancies", "view_own_tasks", "complete_task", "view_reports"},
        "curator": {"view_practices", "manage_vacancies", "view_all_tasks", "view_reports", "export_reports"},
        "teacher": {"view_practices", "create_practice", "edit_practice", "view_all_tasks", "view_reports"},
    }

    for code, desc, section in PERMISSIONS:
        db.session.add(Permission(code=code, description=desc, section=section))
    db.session.flush()

    for role, codes in ROLE_DEFAULTS.items():
        for code in codes:
            perm = Permission.query.filter_by(code=code).first()
            if perm:
                db.session.add(RolePermission(role=role, perm_id=perm.id))

    # ── Уведомления ──
    db.session.add(Notification(user_id=stud1_u.id, message="Добро пожаловать в систему!"))
    db.session.add(Notification(user_id=stud1_u.id, message="Вам назначено задание «Изучить стек технологий организации»"))

    db.session.commit()

    print("=" * 60)
    print("Тестовые данные добавлены.")
    print("=" * 60)
    print()
    print("Учётные записи:")
    print("  admin    / admin123   — Администратор")
    print("  teacher  / teacher123 — Преподаватель (Бычков С.Ю.)")
    print("  teacher2 / teacher123 — Преподаватель (Иванов П.С.)")
    print("  curator  / curator123 — Куратор (Смирнова А.В.)")
    print("  student  / student123 — Студент (Кутенков С.Д.)")
    print("  student2 / student123 — Студент (Эрендженова М.Н.)")
    print("  student3 / student123 — Студент (Дамакальщиков М.А.)")
    print()
    print(f"Данные: {len(orgs)} организации, {len(kafedras)} кафедры,")
    print(f"  {len(komps)} компетенций, 2 практики, 3 вакансии,")
    print(f"  4 задания, 1 комиссия")
