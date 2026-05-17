from datetime import date as _date
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from datetime import datetime
from access.decorators import requires_role
from models import db, Task, Execution, Practice, Student
from helpers import notify

bp = Blueprint("execution", __name__, url_prefix="/execution")


@bp.route("/")
@login_required
def index():
    if current_user.role == "student" and current_user.student:
        tasks = Task.query.filter_by(student_id=current_user.student.id).order_by(Task.created_at.desc()).all()
    elif current_user.role in ("curator", "teacher", "admin"):
        tasks = Task.query.order_by(Task.created_at.desc()).all()
    else:
        tasks = []
    return render_template("execution/index.html", tasks=tasks)


@bp.route("/task/<int:tid>")
@login_required
def task_view(tid):
    t = Task.query.get_or_404(tid)
    return render_template("execution/task_view.html", task=t)


@bp.route("/task/create", methods=["GET", "POST"])
@login_required
@requires_role("curator", "teacher", "admin")
def task_create():
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


@bp.route("/task/<int:tid>/status", methods=["POST"])
@login_required
def change_status(tid):
    t = Task.query.get_or_404(tid)
    new_status = request.form.get("status")
    if new_status in ("in_progress", "pending"):
        t.status = new_status
        db.session.commit()
        flash("Статус обновлён", "success")
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
