from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from access.decorators import requires_role
from models import (db, Vacancy, VacancyRequirement, Application, Distribution,
                     Organization, Practice, Kompetenciya, Student, Teacher, Curator)
from helpers import calc_match, notify

bp = Blueprint("distribution", __name__, url_prefix="/distribution")


@bp.route("/")
@login_required
def index():
    vacancies = Vacancy.query.order_by(Vacancy.id.desc()).all()
    return render_template("distribution/index.html", vacancies=vacancies)


@bp.route("/vacancy/create", methods=["GET", "POST"])
@login_required
@requires_role("curator", "admin")
def vacancy_create():
    orgs = Organization.query.order_by(Organization.name).all()
    practices = Practice.query.order_by(Practice.start_date.desc()).all()
    komps = Kompetenciya.query.order_by(Kompetenciya.name).all()
    if request.method == "POST":
        v = Vacancy(
            title=request.form["title"],
            description=request.form.get("description", ""),
            slots=int(request.form.get("slots", 1)),
            organization_id=request.form.get("organization_id") or None,
            practice_id=request.form.get("practice_id") or None,
        )
        db.session.add(v)
        db.session.flush()
        for k in komps:
            lvl = request.form.get(f"komp_{k.id}")
            if lvl and int(lvl) > 0:
                db.session.add(VacancyRequirement(vacancy_id=v.id, kompetenciya_id=k.id, min_level=int(lvl)))
        db.session.commit()
        flash("Вакансия создана", "success")
        return redirect(url_for("distribution.index"))
    return render_template("distribution/vacancy_form.html", vacancy=None, orgs=orgs, practices=practices, komps=komps)


@bp.route("/vacancy/<int:vid>")
@login_required
def vacancy_view(vid):
    v = Vacancy.query.get_or_404(vid)
    match_pct = None
    already_applied = False
    if current_user.role == "student" and current_user.student:
        match_pct = calc_match(current_user.student.id, vid)
        already_applied = Application.query.filter_by(
            student_id=current_user.student.id, vacancy_id=vid).first() is not None
    return render_template("distribution/vacancy_view.html", v=v, match_pct=match_pct, already_applied=already_applied)


@bp.route("/vacancy/<int:vid>/apply", methods=["POST"])
@login_required
@requires_role("student")
def apply(vid):
    s = current_user.student
    if not s:
        flash("Профиль студента не найден", "danger")
        return redirect(url_for("distribution.index"))
    existing = Application.query.filter_by(student_id=s.id, vacancy_id=vid).first()
    if existing:
        flash("Вы уже подали заявку на эту вакансию", "warning")
        return redirect(url_for("distribution.vacancy_view", vid=vid))
    match = calc_match(s.id, vid)
    app = Application(student_id=s.id, vacancy_id=vid, match_pct=match)
    db.session.add(app)
    db.session.commit()
    flash(f"Заявка подана (совпадение: {match}%)", "success")
    return redirect(url_for("distribution.my_applications"))


@bp.route("/my-applications")
@login_required
@requires_role("student")
def my_applications():
    s = current_user.student
    apps = Application.query.filter_by(student_id=s.id).order_by(Application.created_at.desc()).all() if s else []
    return render_template("distribution/my_applications.html", apps=apps)


@bp.route("/distribute/<int:pid>")
@login_required
@requires_role("teacher", "admin")
def distribute(pid):
    practice = Practice.query.get_or_404(pid)
    vacancies = Vacancy.query.filter_by(practice_id=pid).all()
    apps = []
    for v in vacancies:
        for a in v.applications.filter_by(status="pending").all():
            apps.append(a)
    apps.sort(key=lambda a: a.match_pct, reverse=True)
    return render_template("distribution/distribute.html", practice=practice, apps=apps, vacancies=vacancies)


@bp.route("/distribute/confirm", methods=["POST"])
@login_required
@requires_role("teacher", "admin")
def distribute_confirm():
    app_ids = request.form.getlist("approve")
    for aid in app_ids:
        a = Application.query.get(int(aid))
        if a:
            a.status = "approved"
            d = Distribution(student_id=a.student_id, vacancy_id=a.vacancy_id)
            db.session.add(d)
            if a.student and a.student.user:
                notify(a.student.user.id, f"Вы распределены на вакансию «{a.vacancy.title}»",
                       url_for("distribution.vacancy_view", vid=a.vacancy_id))
    db.session.commit()
    flash("Распределение сохранено", "success")
    return redirect(url_for("distribution.index"))
