from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from datetime import date as _date
from access.decorators import requires_role
from models import db, Practice, PracticeStage, Teacher

def _pd(s):
    """Parse date string YYYY-MM-DD → date."""
    return _date.fromisoformat(s) if s else None

bp = Blueprint("planning", __name__, url_prefix="/planning")


@bp.route("/")
@login_required
def index():
    practices = Practice.query.order_by(Practice.start_date.desc()).all()
    return render_template("planning/index.html", practices=practices)


@bp.route("/create", methods=["GET", "POST"])
@login_required
@requires_role("teacher", "admin")
def create():
    teachers = Teacher.query.order_by(Teacher.last_name).all()
    if request.method == "POST":
        p = Practice(
            name=request.form["name"],
            type=request.form.get("type", ""),
            start_date=_pd(request.form["start_date"]),
            end_date=_pd(request.form["end_date"]),
            description=request.form.get("description", ""),
            teacher_id=request.form.get("teacher_id") or None,
            status="planned",
        )
        db.session.add(p)
        db.session.commit()
        flash("Практика создана", "success")
        return redirect(url_for("planning.index"))
    return render_template("planning/form.html", practice=None, teachers=teachers)


@bp.route("/<int:pid>/edit", methods=["GET", "POST"])
@login_required
@requires_role("teacher", "admin")
def edit(pid):
    p = Practice.query.get_or_404(pid)
    teachers = Teacher.query.order_by(Teacher.last_name).all()
    if request.method == "POST":
        p.name = request.form["name"]
        p.type = request.form.get("type", "")
        p.start_date = _pd(request.form["start_date"])
        p.end_date = _pd(request.form["end_date"])
        p.description = request.form.get("description", "")
        p.teacher_id = request.form.get("teacher_id") or None
        p.status = request.form.get("status", p.status)
        db.session.commit()
        flash("Практика обновлена", "success")
        return redirect(url_for("planning.index"))
    return render_template("planning/form.html", practice=p, teachers=teachers)


@bp.route("/<int:pid>/stages")
@login_required
def stages(pid):
    p = Practice.query.get_or_404(pid)
    return render_template("planning/stages.html", practice=p)


@bp.route("/<int:pid>/stages/add", methods=["GET", "POST"])
@login_required
@requires_role("teacher", "admin")
def stage_add(pid):
    p = Practice.query.get_or_404(pid)
    if request.method == "POST":
        s = PracticeStage(
            practice_id=pid,
            name=request.form["name"],
            start_date=_pd(request.form["start_date"]),
            end_date=_pd(request.form["end_date"]),
            description=request.form.get("description", ""),
            order=len(p.stages) + 1,
        )
        db.session.add(s)
        db.session.commit()
        flash("Этап добавлен", "success")
        return redirect(url_for("planning.stages", pid=pid))
    return render_template("planning/stage_form.html", practice=p, stage=None)


@bp.route("/<int:pid>/stages/<int:sid>/edit", methods=["GET", "POST"])
@login_required
@requires_role("teacher", "admin")
def stage_edit(pid, sid):
    p = Practice.query.get_or_404(pid)
    s = PracticeStage.query.get_or_404(sid)
    if request.method == "POST":
        s.name = request.form["name"]
        s.start_date = _pd(request.form["start_date"])
        s.end_date = _pd(request.form["end_date"])
        s.description = request.form.get("description", "")
        db.session.commit()
        flash("Этап обновлён", "success")
        return redirect(url_for("planning.stages", pid=pid))
    return render_template("planning/stage_form.html", practice=p, stage=s)


@bp.route("/<int:pid>/stages/<int:sid>/delete", methods=["POST"])
@login_required
@requires_role("teacher", "admin")
def stage_delete(pid, sid):
    s = PracticeStage.query.get_or_404(sid)
    db.session.delete(s)
    db.session.commit()
    flash("Этап удалён", "success")
    return redirect(url_for("planning.stages", pid=pid))
