from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

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

    def get_id(self):
        return str(self.id)

    @property
    def active(self):
        return self.is_active

    @property
    def profile(self):
        if self.role == "student":
            return self.student
        if self.role == "teacher":
            return self.teacher
        if self.role == "curator":
            return self.curator
        return None


class Organization(db.Model):
    __tablename__ = "organizations"

    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(256), nullable=False)
    yur_adres = db.Column(db.String(255))

    students = db.relationship("Student", backref="organization")
    curators = db.relationship("Curator", backref="organization")


class Kafedra(db.Model):
    __tablename__ = "kafedras"

    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String(255), nullable=False)
    faculty = db.Column(db.String(100), nullable=False)

    teachers = db.relationship("Teacher", backref="kafedra")
    students = db.relationship("Student", backref="kafedra")


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

    students = db.relationship("Student", backref="teacher")

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
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
        if self.middle_name:
            parts.append(self.middle_name)
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

    tasks = db.relationship("Task", backref="student", lazy="dynamic")

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    @property
    def tasks_done(self):
        return self.tasks.filter_by(status="done").count()

    @property
    def tasks_total(self):
        return self.tasks.count()


class Task(db.Model):
    __tablename__ = "tasks"

    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    title      = db.Column(db.String(256), nullable=False)
    status     = db.Column(db.String(32), nullable=False, default="pending")


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
