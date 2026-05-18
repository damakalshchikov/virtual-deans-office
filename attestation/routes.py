import os
import uuid
from datetime import date as _date, datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from access.decorators import requires_role
from models import (db, Report, Characteristic, Commission, Attestation,
                     Practice, Student, Kafedra)
from helpers import notify

bp = Blueprint("attestation", __name__, url_prefix="/attestation")

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt", "png", "jpg", "jpeg", "zip", "xlsx", "xls"}


def _save_file(file):
    if not file or not file.filename:
        return None, None
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return None, None
    original_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{original_name}"
    upload_dir = os.path.join(current_app.root_path, "static", "uploads", "attestation_files")
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, unique_name))
    return unique_name, original_name


@bp.route("/")
@login_required
def index():
    practices = Practice.query.order_by(Practice.start_date.desc()).all()
    return render_template("attestation/index.html", practices=practices)


# ── Отчёт / Дневник (студент) ────────────────────────────────────────────

@bp.route("/report/submit/<int:pid>", methods=["GET", "POST"])
@login_required
@requires_role("student")
def submit_report(pid):
    p = Practice.query.get_or_404(pid)
    rtype = request.args.get("type", "report")
    if request.method == "POST":
        file_path, file_name = _save_file(request.files.get("file"))
        r = Report(
            student_id=current_user.student.id,
            practice_id=pid,
            type=rtype,
            content=request.form.get("content", ""),
            file_path=file_path,
            file_name=file_name,
            status="submitted",
            submitted_at=datetime.utcnow(),
        )
        db.session.add(r)
        db.session.commit()
        label = "Отчёт" if rtype == "report" else "Дневник"
        flash(f"{label} отправлен", "success")
        return redirect(url_for("attestation.index"))
    return render_template("attestation/report_form.html", practice=p, rtype=rtype)


@bp.route("/report/<int:rid>/review", methods=["GET", "POST"])
@login_required
@requires_role("teacher", "admin")
def review_report(rid):
    r = Report.query.get_or_404(rid)
    if request.method == "POST":
        action = request.form.get("action")
        r.comment = request.form.get("comment", "")
        r.reviewed_at = datetime.utcnow()
        r.status = "approved" if action == "approve" else "rejected"
        db.session.commit()
        if r.student and r.student.user:
            lbl = "Отчёт" if r.type == "report" else "Дневник"
            st = "одобрен" if action == "approve" else "возвращён на доработку"
            notify(r.student.user.id, f"{lbl} по практике «{r.practice.name}» {st}")
        flash("Решение сохранено", "success")
        return redirect(url_for("attestation.practice_detail", pid=r.practice_id))
    return render_template("attestation/review_report.html", report=r)


# ── Характеристика (куратор) ─────────────────────────────────────────────

@bp.route("/characteristic/<int:pid>/<int:sid>", methods=["GET", "POST"])
@login_required
@requires_role("curator")
def characteristic(pid, sid):
    p = Practice.query.get_or_404(pid)
    s = Student.query.get_or_404(sid)
    existing = Characteristic.query.filter_by(student_id=sid, practice_id=pid).first()
    if request.method == "POST":
        file_path, file_name = _save_file(request.files.get("file"))
        if existing:
            existing.content = request.form["content"]
            existing.signed = "signed" in request.form
            if file_path:
                existing.file_path = file_path
                existing.file_name = file_name
        else:
            c = Characteristic(
                student_id=sid, practice_id=pid,
                curator_id=current_user.curator.id,
                content=request.form["content"],
                signed="signed" in request.form,
                file_path=file_path,
                file_name=file_name,
            )
            db.session.add(c)
        db.session.commit()
        flash("Характеристика сохранена", "success")
        return redirect(url_for("attestation.practice_detail", pid=pid))
    return render_template("attestation/characteristic_form.html",
                           practice=p, student=s, char=existing)


@bp.route("/characteristic/<int:cid>")
@login_required
def characteristic_view(cid):
    c = Characteristic.query.get_or_404(cid)
    return render_template("attestation/characteristic_view.html", char=c)


# ── Аттестационный лист ──────────────────────────────────────────────────

@bp.route("/attest/<int:pid>/<int:sid>", methods=["GET", "POST"])
@login_required
@requires_role("teacher", "admin")
def attest(pid, sid):
    p = Practice.query.get_or_404(pid)
    s = Student.query.get_or_404(sid)
    commissions = Commission.query.order_by(Commission.session_date.desc()).all()
    att = Attestation.query.filter_by(student_id=sid, practice_id=pid).first()
    if request.method == "POST":
        if not att:
            att = Attestation(student_id=sid, practice_id=pid)
            db.session.add(att)
        att.commission_id = request.form.get("commission_id") or None
        att.diary_grade = int(request.form.get("diary_grade", 0)) or None
        att.report_grade = int(request.form.get("report_grade", 0)) or None
        att.final_grade = int(request.form.get("final_grade", 0)) or None
        att.recommendation = request.form.get("recommendation", "")
        att.status = "graded"
        db.session.commit()
        flash("Аттестационный лист заполнен", "success")
        return redirect(url_for("attestation.practice_detail", pid=pid))
    return render_template("attestation/attest_form.html",
                           practice=p, student=s, att=att, commissions=commissions)


@bp.route("/attest/<int:aid>/approve", methods=["POST"])
@login_required
@requires_role("teacher", "admin")
def approve_attest(aid):
    att = Attestation.query.get_or_404(aid)
    att.status = "approved"
    db.session.commit()
    if att.student and att.student.user:
        notify(att.student.user.id,
               f"Итоговый результат по практике «{att.practice.name}» утверждён (оценка: {att.final_grade})")
    flash("Результат утверждён", "success")
    return redirect(url_for("attestation.practice_detail", pid=att.practice_id))


# ── Комиссии ─────────────────────────────────────────────────────────────

@bp.route("/commissions")
@login_required
@requires_role("admin")
def commissions():
    items = Commission.query.order_by(Commission.session_date.desc()).all()
    return render_template("attestation/commissions.html", commissions=items)


@bp.route("/commissions/create", methods=["GET", "POST"])
@login_required
@requires_role("admin")
def commission_create():
    kafedras = Kafedra.query.order_by(Kafedra.name).all()
    if request.method == "POST":
        c = Commission(
            name=request.form["name"],
            chairman=request.form["chairman"],
            session_date=_date.fromisoformat(request.form["session_date"]),
            kafedra_id=request.form.get("kafedra_id") or None,
        )
        db.session.add(c)
        db.session.commit()
        flash("Комиссия создана", "success")
        return redirect(url_for("attestation.commissions"))
    return render_template("attestation/commission_form.html", commission=None, kafedras=kafedras)


# ── Детали практики для аттестации ────────────────────────────────────────

@bp.route("/practice/<int:pid>")
@login_required
def practice_detail(pid):
    p = Practice.query.get_or_404(pid)
    students = Student.query.all()
    reports = Report.query.filter_by(practice_id=pid).all()
    chars = Characteristic.query.filter_by(practice_id=pid).all()
    atts = Attestation.query.filter_by(practice_id=pid).all()
    return render_template("attestation/practice_detail.html",
                           practice=p, students=students, reports=reports,
                           chars=chars, atts=atts)
