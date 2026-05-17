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
    curator_org = None
    if current_user.role == "curator" and current_user.curator:
        curator_org = current_user.curator.organization
    orgs = Organization.query.order_by(Organization.name).all() if not curator_org else None
    practices = Practice.query.order_by(Practice.start_date.desc()).all()
    komps = Kompetenciya.query.order_by(Kompetenciya.name).all()
    if request.method == "POST":
        if curator_org:
            org_id = curator_org.id
        else:
            org_id = request.form.get("organization_id") or None
        v = Vacancy(
            title=request.form["title"],
            description=request.form.get("description", ""),
            slots=int(request.form.get("slots", 1)),
            organization_id=org_id,
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
    return render_template("distribution/vacancy_form.html", vacancy=None,
                           orgs=orgs, curator_org=curator_org,
                           practices=practices, komps=komps)


@bp.route("/vacancy/<int:vid>/edit", methods=["GET", "POST"])
@login_required
@requires_role("curator", "admin")
def vacancy_edit(vid):
    v = Vacancy.query.get_or_404(vid)
    curator_org = None
    if current_user.role == "curator" and current_user.curator:
        curator_org = current_user.curator.organization
        if not curator_org or v.organization_id != curator_org.id:
            flash("Вы можете редактировать только вакансии своей организации", "danger")
            return redirect(url_for("distribution.vacancy_view", vid=vid))
    orgs = Organization.query.order_by(Organization.name).all() if not curator_org else None
    practices = Practice.query.order_by(Practice.start_date.desc()).all()
    komps = Kompetenciya.query.order_by(Kompetenciya.name).all()
    if request.method == "POST":
        v.title = request.form["title"]
        v.description = request.form.get("description", "")
        v.slots = int(request.form.get("slots", 1))
        v.practice_id = request.form.get("practice_id") or None
        if not curator_org:
            v.organization_id = request.form.get("organization_id") or None
        VacancyRequirement.query.filter_by(vacancy_id=v.id).delete()
        for k in komps:
            lvl = request.form.get(f"komp_{k.id}")
            if lvl and int(lvl) > 0:
                db.session.add(VacancyRequirement(vacancy_id=v.id, kompetenciya_id=k.id, min_level=int(lvl)))
        db.session.commit()
        flash("Вакансия обновлена", "success")
        return redirect(url_for("distribution.vacancy_view", vid=vid))
    return render_template("distribution/vacancy_form.html", vacancy=v,
                           orgs=orgs, curator_org=curator_org,
                           practices=practices, komps=komps)


@bp.route("/vacancy/<int:vid>/delete", methods=["POST"])
@login_required
@requires_role("curator", "admin")
def vacancy_delete(vid):
    v = Vacancy.query.get_or_404(vid)
    if current_user.role == "curator" and current_user.curator:
        curator_org = current_user.curator.organization
        if not curator_org or v.organization_id != curator_org.id:
            flash("Вы можете удалять только вакансии своей организации", "danger")
            return redirect(url_for("distribution.vacancy_view", vid=vid))
    Distribution.query.filter_by(vacancy_id=vid).delete()
    Application.query.filter_by(vacancy_id=vid).delete()
    db.session.delete(v)
    db.session.commit()
    flash("Вакансия удалена", "success")
    return redirect(url_for("distribution.index"))


@bp.route("/vacancy/<int:vid>")
@login_required
def vacancy_view(vid):
    v = Vacancy.query.get_or_404(vid)
    match_pct = None
    already_applied = False
    already_placed = False
    if current_user.role == "student" and current_user.student:
        s = current_user.student
        match_pct = calc_match(s.id, vid)
        existing_app = Application.query.filter_by(student_id=s.id, vacancy_id=vid).first()
        already_applied = existing_app is not None
        already_placed = Application.query.filter_by(student_id=s.id, status="approved").first() is not None
    return render_template("distribution/vacancy_view.html", v=v, match_pct=match_pct,
                           already_applied=already_applied, already_placed=already_placed)


@bp.route("/vacancy/<int:vid>/apply", methods=["POST"])
@login_required
@requires_role("student")
def apply(vid):
    s = current_user.student
    if not s:
        flash("Профиль студента не найден", "danger")
        return redirect(url_for("distribution.index"))
    if Application.query.filter_by(student_id=s.id, status="approved").first():
        flash("Вы уже приняты на практику и не можете подавать новые заявки", "warning")
        return redirect(url_for("distribution.vacancy_view", vid=vid))
    existing = Application.query.filter_by(student_id=s.id, vacancy_id=vid).first()
    if existing:
        flash("Вы уже подали заявку на эту вакансию", "warning")
        return redirect(url_for("distribution.vacancy_view", vid=vid))
    match = calc_match(s.id, vid)
    app = Application(
        student_id=s.id,
        vacancy_id=vid,
        match_pct=match,
        student_comment=request.form.get("student_comment", "").strip() or None,
    )
    db.session.add(app)
    db.session.commit()
    flash(f"Заявка подана (совпадение: {match}%)", "success")
    return redirect(url_for("distribution.my_applications"))


@bp.route("/application/<int:app_id>/withdraw", methods=["POST"])
@login_required
@requires_role("student")
def withdraw(app_id):
    a = Application.query.get_or_404(app_id)
    if a.student_id != current_user.student.id:
        flash("Нет доступа", "danger")
        return redirect(url_for("distribution.my_applications"))
    if a.status in ("approved", "rejected"):
        flash("Нельзя отозвать уже рассмотренную заявку", "warning")
        return redirect(url_for("distribution.my_applications"))
    db.session.delete(a)
    db.session.commit()
    flash("Заявка отозвана", "success")
    return redirect(url_for("distribution.my_applications"))


@bp.route("/application/<int:app_id>/action", methods=["POST"])
@login_required
@requires_role("curator", "admin")
def application_action(app_id):
    a = Application.query.get_or_404(app_id)
    if current_user.role == "curator" and current_user.curator:
        curator_org = current_user.curator.organization
        if not curator_org or a.vacancy.organization_id != curator_org.id:
            flash("Нет доступа к этой заявке", "danger")
            return redirect(url_for("distribution.index"))
    action = request.form.get("action")
    a.curator_comment = request.form.get("curator_comment", "").strip() or None
    if action == "accept":
        a.status = "approved"
        existing_dist = Distribution.query.filter_by(student_id=a.student_id, vacancy_id=a.vacancy_id).first()
        if not existing_dist:
            db.session.add(Distribution(student_id=a.student_id, vacancy_id=a.vacancy_id))
        s = a.student
        if s:
            s.organization_id = a.vacancy.organization_id
            if current_user.role == "curator" and current_user.curator:
                s.curator_id = current_user.curator.id
            practice = a.vacancy.practice
            if practice:
                s.internship_start = practice.start_date
                s.internship_end = practice.end_date
        msg = f"Ваша заявка на вакансию «{a.vacancy.title}» принята"
    elif action == "reject":
        a.status = "rejected"
        msg = f"Ваша заявка на вакансию «{a.vacancy.title}» отклонена"
    elif action == "interview":
        a.status = "interview"
        msg = f"Вас приглашают на собеседование по вакансии «{a.vacancy.title}»"
    else:
        flash("Неверное действие", "danger")
        return redirect(url_for("distribution.vacancy_view", vid=a.vacancy_id))
    db.session.commit()
    if a.student and a.student.user:
        notify(a.student.user.id, msg, url_for("distribution.vacancy_view", vid=a.vacancy_id))
    flash("Решение сохранено", "success")
    return redirect(url_for("distribution.vacancy_view", vid=a.vacancy_id))


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
