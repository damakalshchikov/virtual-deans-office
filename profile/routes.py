from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Notification

bp = Blueprint("profile", __name__, url_prefix="/profile")


@bp.route("/")
@login_required
def index():
    return render_template("profile/index.html")


@bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "POST":
        p = current_user.profile
        if p:
            p.email = request.form.get("email", "").strip() or None
            if hasattr(p, "last_name"):
                p.last_name = request.form.get("last_name", p.last_name).strip()
                p.first_name = request.form.get("first_name", p.first_name).strip()
                p.middle_name = request.form.get("middle_name", "").strip() or None
            db.session.commit()
            flash("Профиль обновлён", "success")
        return redirect(url_for("profile.index"))
    return render_template("profile/edit.html")


@bp.route("/competencies")
@login_required
def competencies():
    komps = []
    if current_user.role == "student" and current_user.student:
        komps = current_user.student.kompetencii
    return render_template("profile/competencies.html", komps=komps)


@bp.route("/notifications")
@login_required
def notifications():
    notes = current_user.notifications.all()
    return render_template("profile/notifications.html", notes=notes)


@bp.route("/notifications/read/<int:nid>", methods=["POST"])
@login_required
def mark_read(nid):
    n = Notification.query.get_or_404(nid)
    if n.user_id == current_user.id:
        n.is_read = True
        db.session.commit()
    if n.link:
        return redirect(n.link)
    return redirect(url_for("profile.notifications"))


@bp.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    flash("Все уведомления прочитаны", "success")
    return redirect(url_for("profile.notifications"))
