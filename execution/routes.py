import os
import uuid
from datetime import date as _date, datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from access.decorators import requires_role
from models import db, Task, Execution, Practice, Student, TaskComment
from helpers import notify

bp = Blueprint("execution", __name__, url_prefix="/execution")

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt", "png", "jpg", "jpeg", "zip", "xlsx", "xls"}


def _save_file(file):
    if not file or not file.filename:
        return None, None
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return None, None
    original_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{original_name}"
    upload_dir = os.path.join(current_app.root_path, "static", "uploads", "task_files")
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, unique_name))
    return unique_name, original_name


def _get_role_students():
    """Return student IDs visible to the current curator or teacher."""
    if current_user.role == "curator" and current_user.curator:
        org_id = current_user.curator.organization_id
        return [s.id for s in Student.query.filter_by(organization_id=org_id).all()]
    if current_user.role == "teacher" and current_user.teacher:
        return [s.id for s in Student.query.filter_by(teacher_id=current_user.teacher.id).all()]
    return None  # admin sees all


def _can_manage_task(task):
    if current_user.role == "admin":
        return True
    ids = _get_role_students()
    return ids is not None and task.student_id in ids


@bp.route("/")
@login_required
def index():
    if current_user.role == "student" and current_user.student:
        tasks = Task.query.filter_by(student_id=current_user.student.id).order_by(Task.created_at.desc()).all()
    elif current_user.role == "admin":
        tasks = Task.query.order_by(Task.created_at.desc()).all()
    else:
        ids = _get_role_students()
        tasks = Task.query.filter(Task.student_id.in_(ids)).order_by(Task.created_at.desc()).all() if ids else []
    return render_template("execution/index.html", tasks=tasks)


@bp.route("/task/<int:tid>")
@login_required
def task_view(tid):
    t = Task.query.get_or_404(tid)
    can_manage = current_user.role in ("curator", "teacher", "admin") and _can_manage_task(t)
    return render_template("execution/task_view.html", task=t, can_manage=can_manage)


@bp.route("/task/create", methods=["GET", "POST"])
@login_required
@requires_role("curator", "teacher", "admin")
def task_create():
    ids = _get_role_students()
    if ids is not None:
        students = Student.query.filter(Student.id.in_(ids)).order_by(Student.last_name).all()
    else:
        students = Student.query.order_by(Student.last_name).all()
    practices = Practice.query.order_by(Practice.start_date.desc()).all()
    if request.method == "POST":
        t = Task(
            title=request.form["title"],
            description=request.form.get("description", ""),
            student_id=request.form.get("student_id") or None,
            practice_id=request.form.get("practice_id") or None,
            due_date=_date.fromisoformat(request.form["due_date"]) if request.form.get("due_date") else None,
        )
        db.session.add(t)
        db.session.commit()
        if t.student_id:
            s = Student.query.get(t.student_id)
            if s and s.user:
                notify(s.user.id, f"Вам назначено задание «{t.title}»",
                       url_for("execution.task_view", tid=t.id))
        flash("Задание создано", "success")
        return redirect(url_for("execution.index"))
    return render_template("execution/task_form.html", task=None, students=students, practices=practices)


@bp.route("/task/<int:tid>/edit", methods=["GET", "POST"])
@login_required
@requires_role("curator", "teacher", "admin")
def task_edit(tid):
    t = Task.query.get_or_404(tid)
    if not _can_manage_task(t):
        flash("Нет доступа к этому заданию", "danger")
        return redirect(url_for("execution.index"))
    ids = _get_role_students()
    if ids is not None:
        students = Student.query.filter(Student.id.in_(ids)).order_by(Student.last_name).all()
    else:
        students = Student.query.order_by(Student.last_name).all()
    practices = Practice.query.order_by(Practice.start_date.desc()).all()
    if request.method == "POST":
        t.title = request.form["title"]
        t.description = request.form.get("description", "")
        t.due_date = _date.fromisoformat(request.form["due_date"]) if request.form.get("due_date") else None
        db.session.commit()
        flash("Задание обновлено", "success")
        return redirect(url_for("execution.task_view", tid=tid))
    return render_template("execution/task_form.html", task=t, students=students, practices=practices)


@bp.route("/task/<int:tid>/status", methods=["POST"])
@login_required
def change_status(tid):
    t = Task.query.get_or_404(tid)
    new_status = request.form.get("status")
    if current_user.role == "student":
        if new_status in ("in_progress", "pending") and t.student_id == current_user.student.id:
            t.status = new_status
            db.session.commit()
            flash("Статус обновлён", "success")
    elif _can_manage_task(t):
        valid = ("pending", "in_progress", "submitted", "accepted", "rejected")
        if new_status in valid:
            t.status = new_status
            db.session.commit()
            flash("Статус обновлён", "success")
            if t.student and t.student.user:
                labels = {"accepted": "принято", "rejected": "отклонено"}
                if new_status in labels:
                    notify(t.student.user.id, f"Задание «{t.title}» {labels[new_status]}",
                           url_for("execution.task_view", tid=tid))
    return redirect(url_for("execution.task_view", tid=tid))


@bp.route("/task/<int:tid>/comment", methods=["POST"])
@login_required
def add_comment(tid):
    t = Task.query.get_or_404(tid)
    if current_user.role == "student":
        if not t.student_id or t.student_id != current_user.student.id:
            flash("Нет доступа", "danger")
            return redirect(url_for("execution.index"))
    elif not _can_manage_task(t):
        flash("Нет доступа", "danger")
        return redirect(url_for("execution.index"))

    content = request.form.get("content", "").strip()
    file = request.files.get("file")
    file_path, file_name = _save_file(file)

    if not content and not file_path:
        flash("Добавьте текст или файл", "warning")
        return redirect(url_for("execution.task_view", tid=tid))

    c = TaskComment(task_id=tid, user_id=current_user.id, content=content or None,
                    file_path=file_path, file_name=file_name)
    db.session.add(c)
    db.session.commit()
    flash("Комментарий добавлен", "success")
    return redirect(url_for("execution.task_view", tid=tid))


@bp.route("/task/<int:tid>/submit", methods=["GET", "POST"])
@login_required
@requires_role("student")
def submit_result(tid):
    t = Task.query.get_or_404(tid)
    if request.method == "POST":
        e = Execution(
            task_id=tid,
            student_id=current_user.student.id,
            content=request.form.get("content", ""),
        )
        db.session.add(e)
        t.status = "submitted"
        db.session.commit()
        flash("Результат отправлен на проверку", "success")
        return redirect(url_for("execution.task_view", tid=tid))
    return render_template("execution/submit.html", task=t)


@bp.route("/task/<int:tid>/review/<int:eid>", methods=["GET", "POST"])
@login_required
@requires_role("curator", "teacher", "admin")
def review(tid, eid):
    t = Task.query.get_or_404(tid)
    e = Execution.query.get_or_404(eid)
    if request.method == "POST":
        action = request.form.get("action")
        e.comment = request.form.get("comment", "")
        e.reviewed_at = datetime.utcnow()
        if action == "accept":
            e.status = "accepted"
            t.status = "accepted"
            flash("Работа принята", "success")
        else:
            e.status = "rejected"
            t.status = "rejected"
            flash("Работа отклонена", "warning")
        db.session.commit()
        if t.student and t.student.user:
            msg = "принята" if action == "accept" else "отклонена"
            notify(t.student.user.id, f"Работа по заданию «{t.title}» {msg}",
                   url_for("execution.task_view", tid=tid))
        return redirect(url_for("execution.task_view", tid=tid))
    return render_template("execution/review.html", task=t, execution=e)
