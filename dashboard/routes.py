from datetime import date as _date
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import (db, User, Student, Teacher, Curator, Organization, Kafedra,
                     Permission, RolePermission, Kompetenciya, StudentKompetenciya,
                     Distribution)
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
        accepted_practice = None
        if student:
            dist = Distribution.query.filter_by(student_id=student.id).order_by(Distribution.created_at.desc()).first()
            if dist and dist.vacancy and dist.vacancy.practice:
                accepted_practice = dist.vacancy.practice
        return render_template("dashboard/student.html", student=student, accepted_practice=accepted_practice)
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


# ── Admin: Пользователи ─────────────────────────────────────────────────

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
            flash("Пользователь уже существует", "danger")
        else:
            user = User(login=login_val, password=generate_password_hash(password), role=role)
            db.session.add(user)
            db.session.commit()
            flash(f"Пользователь {login_val} создан", "success")
            return redirect(url_for("dashboard.admin_users"))
    return render_template("dashboard/admin_user_form.html", roles=["student", "curator", "teacher", "admin"])


@bp.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@requires_role("admin")
def admin_user_toggle(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Нельзя деактивировать себя", "warning")
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash(f"Пользователь {'активирован' if user.is_active else 'деактивирован'}", "success")
    return redirect(url_for("dashboard.admin_users"))


@bp.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@requires_role("admin")
def admin_user_edit(user_id):
    user = User.query.get_or_404(user_id)
    kafedras = Kafedra.query.order_by(Kafedra.name).all()
    organizations = Organization.query.order_by(Organization.name).all()
    teachers = Teacher.query.order_by(Teacher.last_name).all()
    curators = Curator.query.order_by(Curator.last_name).all()

    if request.method == "POST":
        new_login = request.form.get("login", "").strip()
        if not new_login:
            flash("Логин не может быть пустым", "danger")
            return render_template("dashboard/admin_user_edit.html", user=user, kafedras=kafedras,
                                   organizations=organizations, teachers=teachers, curators=curators)
        if new_login != user.login and User.query.filter_by(login=new_login).first():
            flash(f"Логин «{new_login}» занят", "danger")
            return render_template("dashboard/admin_user_edit.html", user=user, kafedras=kafedras,
                                   organizations=organizations, teachers=teachers, curators=curators)
        user.login = new_login
        pw = request.form.get("password", "").strip()
        if pw:
            user.password = generate_password_hash(pw)

        if user.role == "student":
            p = user.student or Student(user_id=user.id, last_name="", first_name="", group_name="")
            if not user.student:
                db.session.add(p)
                db.session.flush()
            p.last_name = request.form.get("last_name", "").strip()
            p.first_name = request.form.get("first_name", "").strip()
            p.middle_name = request.form.get("middle_name", "").strip() or None
            p.group_name = request.form.get("group_name", p.group_name).strip()
            p.specialty = request.form.get("specialty", "").strip() or None
            p.email = request.form.get("email", "").strip() or None
            p.average_grade = request.form.get("average_grade") or None
            p.kafedra_id = request.form.get("kafedra_id") or None
            p.internship_start = _date.fromisoformat(request.form["internship_start"]) if request.form.get("internship_start") else None
            p.internship_end = _date.fromisoformat(request.form["internship_end"]) if request.form.get("internship_end") else None
            p.organization_id = request.form.get("organization_id") or None
            p.teacher_id = request.form.get("teacher_id") or None
            p.curator_id = request.form.get("curator_id") or None
        elif user.role == "teacher":
            p = user.teacher or Teacher(user_id=user.id, last_name="", first_name="")
            if not user.teacher:
                db.session.add(p)
                db.session.flush()
            p.last_name = request.form.get("last_name", "").strip()
            p.first_name = request.form.get("first_name", "").strip()
            p.middle_name = request.form.get("middle_name", "").strip() or None
            p.position = request.form.get("position", "").strip() or None
            p.email = request.form.get("email", "").strip() or None
            p.kafedra_id = request.form.get("kafedra_id") or None
        elif user.role == "curator":
            p = user.curator or Curator(user_id=user.id, last_name="", first_name="")
            if not user.curator:
                db.session.add(p)
                db.session.flush()
            p.last_name = request.form.get("last_name", "").strip()
            p.first_name = request.form.get("first_name", "").strip()
            p.middle_name = request.form.get("middle_name", "").strip() or None
            p.position = request.form.get("position", "").strip() or None
            p.email = request.form.get("email", "").strip() or None
            p.organization_id = request.form.get("organization_id") or None

        new_role = request.form.get("role", "")
        if new_role in ("student", "curator", "teacher", "admin"):
            user.role = new_role
        db.session.commit()
        flash(f"Данные обновлены", "success")
        return redirect(url_for("dashboard.admin_users"))

    return render_template("dashboard/admin_user_edit.html", user=user, kafedras=kafedras,
                           organizations=organizations, teachers=teachers, curators=curators)


# ── Admin: Права доступа ─────────────────────────────────────────────────

@bp.route("/admin/permissions", methods=["GET", "POST"])
@login_required
@requires_role("admin")
def admin_permissions():
    roles = ["student", "curator", "teacher", "admin"]
    if request.method == "POST":
        RolePermission.query.filter(RolePermission.role != "admin").delete()
        for role in roles:
            if role == "admin":
                continue
            for perm in Permission.query.all():
                if request.form.get(f"{role}_{perm.id}"):
                    db.session.add(RolePermission(role=role, perm_id=perm.id))
        db.session.commit()
        flash("Права обновлены", "success")
        return redirect(url_for("dashboard.admin_permissions"))

    permissions = Permission.query.order_by(Permission.section, Permission.id).all()
    sections = {}
    for p in permissions:
        sections.setdefault(p.section, []).append(p)
    assigned = {(rp.role, rp.perm_id) for rp in RolePermission.query.all()}
    for perm in permissions:
        assigned.add(("admin", perm.id))
    return render_template("dashboard/admin_permissions.html", roles=roles, sections=sections, assigned=assigned)


# ── Admin: Справочник кафедр ─────────────────────────────────────────────

@bp.route("/admin/kafedras")
@login_required
@requires_role("admin")
def admin_kafedras():
    items = Kafedra.query.order_by(Kafedra.name).all()
    return render_template("dashboard/admin_ref.html", title="Кафедры", icon="building-columns",
                           items=items, type="kafedra")


@bp.route("/admin/kafedras/save", methods=["POST"])
@login_required
@requires_role("admin")
def admin_kafedra_save():
    kid = request.form.get("id")
    if kid:
        k = Kafedra.query.get_or_404(int(kid))
    else:
        k = Kafedra(name="", faculty="")
        db.session.add(k)
    k.name = request.form["name"]
    k.faculty = request.form["faculty"]
    db.session.commit()
    flash("Сохранено", "success")
    return redirect(url_for("dashboard.admin_kafedras"))


# ── Admin: Справочник организаций ────────────────────────────────────────

@bp.route("/admin/orgs")
@login_required
@requires_role("admin")
def admin_orgs():
    items = Organization.query.order_by(Organization.name).all()
    return render_template("dashboard/admin_ref.html", title="Организации", icon="city",
                           items=items, type="org")


@bp.route("/admin/orgs/save", methods=["POST"])
@login_required
@requires_role("admin")
def admin_org_save():
    oid = request.form.get("id")
    if oid:
        o = Organization.query.get_or_404(int(oid))
    else:
        o = Organization(name="")
        db.session.add(o)
    o.name = request.form["name"]
    o.yur_adres = request.form.get("yur_adres", "")
    db.session.commit()
    flash("Сохранено", "success")
    return redirect(url_for("dashboard.admin_orgs"))


# ── Admin: Справочник компетенций ────────────────────────────────────────

@bp.route("/admin/komps")
@login_required
@requires_role("admin")
def admin_komps():
    items = Kompetenciya.query.order_by(Kompetenciya.name).all()
    return render_template("dashboard/admin_ref.html", title="Компетенции", icon="brain",
                           items=items, type="komp")


@bp.route("/admin/komps/save", methods=["POST"])
@login_required
@requires_role("admin")
def admin_komp_save():
    kid = request.form.get("id")
    if kid:
        k = Kompetenciya.query.get_or_404(int(kid))
    else:
        k = Kompetenciya(name="")
        db.session.add(k)
    k.name = request.form["name"]
    db.session.commit()
    flash("Сохранено", "success")
    return redirect(url_for("dashboard.admin_komps"))


# ── Admin: Компетенции студента ──────────────────────────────────────────

@bp.route("/admin/student-komps/<int:sid>", methods=["GET", "POST"])
@login_required
@requires_role("admin")
def admin_student_komps(sid):
    student = Student.query.get_or_404(sid)
    komps = Kompetenciya.query.order_by(Kompetenciya.name).all()
    current_levels = {sk.kompetenciya_id: sk.level for sk in student.kompetencii}
    if request.method == "POST":
        StudentKompetenciya.query.filter_by(student_id=sid).delete()
        for k in komps:
            lvl = request.form.get(f"level_{k.id}", "0")
            if int(lvl) > 0:
                db.session.add(StudentKompetenciya(student_id=sid, kompetenciya_id=k.id, level=int(lvl)))
        db.session.commit()
        flash("Компетенции обновлены", "success")
        return redirect(url_for("dashboard.admin_users"))
    return render_template("dashboard/admin_student_komps.html",
                           student=student, komps=komps, current_levels=current_levels)
