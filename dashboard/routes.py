from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User

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
