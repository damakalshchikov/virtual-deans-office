from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import date, datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id        = db.Column(db.Integer, primary_key=True)
    login     = db.Column(db.String(64), unique=True, nullable=False)
    password  = db.Column(db.String(256), nullable=False)
    role      = db.Column(db.String(32), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    student = db.relationship("Student", backref="user", uselist=False)
    teacher = db.relationship("Teacher", backref="user", uselist=False)
    curator = db.relationship("Curator", backref="user", uselist=False)
    notifications = db.relationship("Notification", backref="user", lazy="dynamic",
                                     order_by="Notification.created_at.desc()")
    def get_id(self): return str(self.id)
    @property
    def active(self): return self.is_active
    @property
    def profile(self):
        return {"student": self.student, "teacher": self.teacher,
                "curator": self.curator}.get(self.role)
    @property
    def unread_count(self):
        return self.notifications.filter_by(is_read=False).count()


class Permission(db.Model):
    __tablename__ = "permissions"
    id          = db.Column(db.Integer, primary_key=True)
    code        = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256), nullable=False)
    section     = db.Column(db.String(64), nullable=False)
    role_permissions = db.relationship("RolePermission", backref="permission",
                                        cascade="all, delete-orphan")

class RolePermission(db.Model):
    __tablename__ = "role_permissions"
    role    = db.Column(db.String(32), primary_key=True)
    perm_id = db.Column(db.Integer, db.ForeignKey("permissions.id"), primary_key=True)


class Organization(db.Model):
    __tablename__ = "organizations"
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(256), nullable=False)
    yur_adres = db.Column(db.String(255))
    students  = db.relationship("Student", backref="organization")
    curators  = db.relationship("Curator", backref="organization")
    vacancies = db.relationship("Vacancy", backref="organization")


class Kafedra(db.Model):
    __tablename__ = "kafedras"
    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String(255), nullable=False)
    faculty = db.Column(db.String(100), nullable=False)
    teachers = db.relationship("Teacher", backref="kafedra")
    students = db.relationship("Student", backref="kafedra")


class Kompetenciya(db.Model):
    __tablename__ = "kompetencii"
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    student_links  = db.relationship("StudentKompetenciya", backref="kompetenciya", cascade="all, delete-orphan")
    vacancy_links  = db.relationship("VacancyRequirement", backref="kompetenciya", cascade="all, delete-orphan")


class Teacher(db.Model):
    __tablename__ = "teachers"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True)
    last_name   = db.Column(db.String(64), nullable=False)
    first_name  = db.Column(db.String(64), nullable=False)
    middle_name = db.Column(db.String(64))
    position    = db.Column(db.String(100))
    email       = db.Column(db.String(100))
    kafedra_id  = db.Column(db.Integer, db.ForeignKey("kafedras.id"))
    students    = db.relationship("Student", backref="teacher")
    practices   = db.relationship("Practice", backref="teacher")
    @property
    def full_name(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name: parts.append(self.middle_name)
        return " ".join(parts)


class Curator(db.Model):
    __tablename__ = "curators"
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True)
    last_name       = db.Column(db.String(64), nullable=False)
    first_name      = db.Column(db.String(64), nullable=False)
    middle_name     = db.Column(db.String(64))
    position        = db.Column(db.String(100))
    email           = db.Column(db.String(100))
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"))
    students = db.relationship("Student", backref="curator")
    @property
    def full_name(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name: parts.append(self.middle_name)
        return " ".join(parts)


class Student(db.Model):
    __tablename__ = "students"
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True)
    last_name        = db.Column(db.String(64), nullable=False)
    first_name       = db.Column(db.String(64), nullable=False)
    middle_name      = db.Column(db.String(64))
    group_name       = db.Column(db.String(64), nullable=False)
    specialty        = db.Column(db.String(256))
    email            = db.Column(db.String(255))
    average_grade    = db.Column(db.Numeric(3, 2))
    kafedra_id       = db.Column(db.Integer, db.ForeignKey("kafedras.id"))
    internship_start = db.Column(db.Date)
    internship_end   = db.Column(db.Date)
    organization_id  = db.Column(db.Integer, db.ForeignKey("organizations.id"))
    teacher_id       = db.Column(db.Integer, db.ForeignKey("teachers.id"))
    curator_id       = db.Column(db.Integer, db.ForeignKey("curators.id"))
    tasks          = db.relationship("Task", backref="student", lazy="dynamic")
    kompetencii    = db.relationship("StudentKompetenciya", backref="student", cascade="all, delete-orphan")
    applications   = db.relationship("Application", backref="student", lazy="dynamic")
    @property
    def full_name(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name: parts.append(self.middle_name)
        return " ".join(parts)
    @property
    def tasks_done(self): return self.tasks.filter_by(status="accepted").count()
    @property
    def tasks_total(self): return self.tasks.count()


class StudentKompetenciya(db.Model):
    __tablename__ = "student_kompetencii"
    student_id      = db.Column(db.Integer, db.ForeignKey("students.id"), primary_key=True)
    kompetenciya_id = db.Column(db.Integer, db.ForeignKey("kompetencii.id"), primary_key=True)
    level           = db.Column(db.Integer, nullable=False, default=1)


class Practice(db.Model):
    __tablename__ = "practices"
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(256), nullable=False)
    type        = db.Column(db.String(100))
    start_date  = db.Column(db.Date, nullable=False)
    end_date    = db.Column(db.Date, nullable=False)
    status      = db.Column(db.String(32), default="planned")
    teacher_id  = db.Column(db.Integer, db.ForeignKey("teachers.id"))
    description = db.Column(db.Text)
    stages    = db.relationship("PracticeStage", backref="practice", cascade="all, delete-orphan",
                                 order_by="PracticeStage.order")
    vacancies = db.relationship("Vacancy", backref="practice")
    tasks     = db.relationship("Task", backref="practice")


class PracticeStage(db.Model):
    __tablename__ = "practice_stages"
    id          = db.Column(db.Integer, primary_key=True)
    practice_id = db.Column(db.Integer, db.ForeignKey("practices.id"), nullable=False)
    name        = db.Column(db.String(255), nullable=False)
    start_date  = db.Column(db.Date, nullable=False)
    end_date    = db.Column(db.Date, nullable=False)
    order       = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)


class Vacancy(db.Model):
    __tablename__ = "vacancies"
    id              = db.Column(db.Integer, primary_key=True)
    title           = db.Column(db.String(256), nullable=False)
    description     = db.Column(db.Text)
    slots           = db.Column(db.Integer, default=1)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"))
    practice_id     = db.Column(db.Integer, db.ForeignKey("practices.id"))
    status          = db.Column(db.String(32), default="open")
    requirements = db.relationship("VacancyRequirement", backref="vacancy", cascade="all, delete-orphan")
    applications = db.relationship("Application", backref="vacancy", lazy="dynamic")
    distributions = db.relationship("Distribution", backref="vacancy")


class VacancyRequirement(db.Model):
    __tablename__ = "vacancy_requirements"
    vacancy_id      = db.Column(db.Integer, db.ForeignKey("vacancies.id"), primary_key=True)
    kompetenciya_id = db.Column(db.Integer, db.ForeignKey("kompetencii.id"), primary_key=True)
    min_level       = db.Column(db.Integer, default=1)


class Application(db.Model):
    __tablename__ = "applications"
    id              = db.Column(db.Integer, primary_key=True)
    student_id      = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    vacancy_id      = db.Column(db.Integer, db.ForeignKey("vacancies.id"), nullable=False)
    status          = db.Column(db.String(32), default="pending")
    match_pct       = db.Column(db.Integer, default=0)
    student_comment = db.Column(db.Text)
    curator_comment = db.Column(db.Text)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("student_id", "vacancy_id"),)


class Distribution(db.Model):
    __tablename__ = "distributions"
    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    vacancy_id = db.Column(db.Integer, db.ForeignKey("vacancies.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"))
    curator_id = db.Column(db.Integer, db.ForeignKey("curators.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship("Student", backref="distributions")


class Task(db.Model):
    __tablename__ = "tasks"
    id          = db.Column(db.Integer, primary_key=True)
    student_id  = db.Column(db.Integer, db.ForeignKey("students.id"))
    practice_id = db.Column(db.Integer, db.ForeignKey("practices.id"))
    title       = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    status      = db.Column(db.String(32), nullable=False, default="pending")
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    due_date    = db.Column(db.Date)
    executions = db.relationship("Execution", backref="task", cascade="all, delete-orphan",
                                  order_by="Execution.submitted_at.desc()")


class Execution(db.Model):
    __tablename__ = "executions"
    id           = db.Column(db.Integer, primary_key=True)
    task_id      = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    student_id   = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    content      = db.Column(db.Text)
    file_path    = db.Column(db.String(512))
    status       = db.Column(db.String(32), default="submitted")
    comment      = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at  = db.Column(db.DateTime)
    student_rel  = db.relationship("Student", backref="executions_list")


class Report(db.Model):
    __tablename__ = "reports"
    id          = db.Column(db.Integer, primary_key=True)
    student_id  = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    practice_id = db.Column(db.Integer, db.ForeignKey("practices.id"), nullable=False)
    type        = db.Column(db.String(32), nullable=False)
    content     = db.Column(db.Text)
    file_path   = db.Column(db.String(512))
    status      = db.Column(db.String(32), default="draft")
    submitted_at = db.Column(db.DateTime)
    reviewed_at  = db.Column(db.DateTime)
    comment      = db.Column(db.Text)
    student  = db.relationship("Student", backref="reports")
    practice = db.relationship("Practice", backref="reports")


class Characteristic(db.Model):
    __tablename__ = "characteristics"
    id          = db.Column(db.Integer, primary_key=True)
    student_id  = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    practice_id = db.Column(db.Integer, db.ForeignKey("practices.id"), nullable=False)
    curator_id  = db.Column(db.Integer, db.ForeignKey("curators.id"), nullable=False)
    content     = db.Column(db.Text, nullable=False)
    signed      = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    student  = db.relationship("Student", backref="characteristics")
    practice = db.relationship("Practice", backref="characteristics")
    curator  = db.relationship("Curator", backref="characteristics")


class Commission(db.Model):
    __tablename__ = "commissions"
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(255), nullable=False)
    chairman     = db.Column(db.String(255), nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    kafedra_id   = db.Column(db.Integer, db.ForeignKey("kafedras.id"))
    kafedra      = db.relationship("Kafedra", backref="commissions")
    attestations = db.relationship("Attestation", backref="commission")


class Attestation(db.Model):
    __tablename__ = "attestations"
    id              = db.Column(db.Integer, primary_key=True)
    student_id      = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    practice_id     = db.Column(db.Integer, db.ForeignKey("practices.id"), nullable=False)
    commission_id   = db.Column(db.Integer, db.ForeignKey("commissions.id"))
    diary_grade     = db.Column(db.Integer)
    report_grade    = db.Column(db.Integer)
    final_grade     = db.Column(db.Integer)
    recommendation  = db.Column(db.Text)
    status          = db.Column(db.String(32), default="pending")
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    student  = db.relationship("Student", backref="attestations")
    practice = db.relationship("Practice", backref="attestations")


class Notification(db.Model):
    __tablename__ = "notifications"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message    = db.Column(db.String(512), nullable=False)
    link       = db.Column(db.String(256))
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
