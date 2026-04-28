from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User, Student, Teacher, Curator, Organization, Kafedra, Permission, RolePermission

from access.decorators import requires_role

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def root():
    return redirect(url_for("dashboard.index"))


@bp.route("/dashboard")
@login_required
def index():
    role = current_user.role

    if role == "student":
        student = current_user.student
        return render_template("dashboard/student.html", student=student)

    if role == "curator":
        curator = current_user.curator
        students = curator.students if curator else []
        return render_template("dashboard/curator.html", curator=curator, students=students)

    if role == "teacher":
        teacher = current_user.teacher
        students = teacher.students if teacher else []
        return render_template("dashboard/teacher.html", teacher=teacher, students=students)

    if role == "admin":
        users = User.query.order_by(User.id).all()
        return render_template("dashboard/admin.html", users=users)

    abort(403)


# Admin: Список пользователей

@bp.route("/admin/users")
@login_required
@requires_role("admin")
def admin_users():
    users = User.query.order_by(User.id).all()
    return render_template("dashboard/admin.html", users=users)


@bp.route("/admin/users/new", methods=["GET", "POST"])
@login_required
@requires_role("admin")
def admin_user_create():
    roles = ["student", "curator", "teacher", "admin"]
    if request.method == "POST":
        login_val = request.form.get("login", "").strip()
        password  = request.form.get("password", "")
        role      = request.form.get("role", "")

        if not login_val or not password or role not in roles:
            flash("Заполните все поля корректно", "danger")
        elif User.query.filter_by(login=login_val).first():
            flash("Пользователь с таким логином уже существует", "danger")
        else:
            user = User(
                login=login_val,
                password=generate_password_hash(password),
                role=role,
            )
            db.session.add(user)
            db.session.commit()
            flash(f"Пользователь {login_val} создан", "success")
            return redirect(url_for("dashboard.admin_users"))

    return render_template("dashboard/admin_user_form.html", roles=roles)


@bp.route("/admin/users/<int:user_id>/role", methods=["POST"])
@login_required
@requires_role("admin")
def admin_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role", "")
    if new_role in ("student", "curator", "teacher", "admin"):
        user.role = new_role
        db.session.commit()
        flash(f"Роль пользователя {user.login} изменена на «{new_role}»", "success")
    return redirect(url_for("dashboard.admin_users"))


@bp.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@requires_role("admin")
def admin_user_toggle(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Нельзя деактивировать собственную учётную запись", "warning")
    else:
        user.is_active = not user.is_active
        db.session.commit()
        state = "активирован" if user.is_active else "деактивирован"
        flash(f"Пользователь {user.login} {state}", "success")
    return redirect(url_for("dashboard.admin_users"))


@bp.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@requires_role("admin")
def admin_user_edit(user_id):
    user = User.query.get_or_404(user_id)
    kafedras      = Kafedra.query.order_by(Kafedra.name).all()
    organizations = Organization.query.order_by(Organization.name).all()
    teachers      = Teacher.query.order_by(Teacher.last_name, Teacher.first_name).all()
    curators      = Curator.query.order_by(Curator.last_name, Curator.first_name).all()

    if request.method == "POST":
        new_login = request.form.get("login", "").strip()
        if not new_login:
            flash("Логин не может быть пустым", "danger")
            return render_template(
                "dashboard/admin_user_edit.html",
                user=user, kafedras=kafedras,
                organizations=organizations, teachers=teachers, curators=curators,
            )
        if new_login != user.login and User.query.filter_by(login=new_login).first():
            flash(f"Логин «{new_login}» уже занят", "danger")
            return render_template(
                "dashboard/admin_user_edit.html",
                user=user, kafedras=kafedras,
                organizations=organizations, teachers=teachers, curators=curators,
            )
        user.login = new_login

        new_password = request.form.get("password", "").strip()
        if new_password:
            user.password = generate_password_hash(new_password)

        if user.role == "student":
            profile = user.student
            if profile is None:
                profile = Student(user_id=user.id, last_name="", first_name="", group_name="")
                db.session.add(profile)
                db.session.flush()
            profile.last_name        = request.form.get("last_name", "").strip()
            profile.first_name       = request.form.get("first_name", "").strip()
            profile.middle_name      = request.form.get("middle_name", "").strip() or None
            profile.group_name       = request.form.get("group_name", profile.group_name).strip()
            profile.specialty        = request.form.get("specialty", "").strip() or None
            profile.email            = request.form.get("email", "").strip() or None
            profile.average_grade    = request.form.get("average_grade") or None
            profile.kafedra_id       = request.form.get("kafedra_id") or None
            profile.internship_start = request.form.get("internship_start") or None
            profile.internship_end   = request.form.get("internship_end") or None
            profile.organization_id  = request.form.get("organization_id") or None
            profile.teacher_id       = request.form.get("teacher_id") or None
            profile.curator_id       = request.form.get("curator_id") or None

        elif user.role == "teacher":
            profile = user.teacher
            if profile is None:
                profile = Teacher(user_id=user.id, last_name="", first_name="")
                db.session.add(profile)
                db.session.flush()
            profile.last_name   = request.form.get("last_name", "").strip()
            profile.first_name  = request.form.get("first_name", "").strip()
            profile.middle_name = request.form.get("middle_name", "").strip() or None
            profile.position    = request.form.get("position", "").strip() or None
            profile.email       = request.form.get("email", "").strip() or None
            profile.kafedra_id  = request.form.get("kafedra_id") or None

        elif user.role == "curator":
            profile = user.curator
            if profile is None:
                profile = Curator(user_id=user.id, last_name="", first_name="")
                db.session.add(profile)
                db.session.flush()
            profile.last_name       = request.form.get("last_name", "").strip()
            profile.first_name      = request.form.get("first_name", "").strip()
            profile.middle_name     = request.form.get("middle_name", "").strip() or None
            profile.position        = request.form.get("position", "").strip() or None
            profile.email           = request.form.get("email", "").strip() or None
            profile.organization_id = request.form.get("organization_id") or None

        new_role = request.form.get("role", "")
        if new_role in ("student", "curator", "teacher", "admin"):
            user.role = new_role

        db.session.commit()
        flash(f"Данные пользователя {user.login} обновлены", "success")
        return redirect(url_for("dashboard.admin_users"))

    return render_template(
        "dashboard/admin_user_edit.html",
        user=user,
        kafedras=kafedras,
        organizations=organizations,
        teachers=teachers,
        curators=curators,
    )


# Admin: Управление правами доступа

@bp.route("/admin/permissions", methods=["GET", "POST"])
@login_required
@requires_role("admin")
def admin_permissions():
    """Управление правами доступа по ролям."""
    roles = ["student", "curator", "teacher", "admin"]

    if request.method == "POST":
        # Удаляем все текущие права для ролей (кроме admin)
        RolePermission.query.filter(RolePermission.role != "admin").delete()
        
        for role in roles:
            if role == "admin":
                # Администратор всегда имеет все права (они не хранятся в БД)
                continue
            for perm in Permission.query.all():
                key = f"{role}_{perm.id}"
                if request.form.get(key):
                    db.session.add(RolePermission(role=role, perm_id=perm.id))
        
        db.session.commit()
        flash("Права доступа обновлены", "success")
        return redirect(url_for("dashboard.admin_permissions"))

    # Строим словарь: {section: [permission, ...]}
    permissions = Permission.query.order_by(Permission.section, Permission.id).all()
    sections = {}
    for p in permissions:
        sections.setdefault(p.section, []).append(p)

    # Текущие назначения: set of (role, perm_id)
    assigned = {
        (rp.role, rp.perm_id)
        for rp in RolePermission.query.all()
    }
    
    # Все права у администратора
    for perm in permissions:
        assigned.add(("admin", perm.id))

    return render_template(
        "dashboard/admin_permissions.html",
        roles=roles,
        sections=sections,
        assigned=assigned,
    )
