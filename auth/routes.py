from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import User

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        login_val = request.form.get("login", "").strip()
        password  = request.form.get("password", "")

        user = User.query.filter_by(login=login_val).first()
        if user and user.is_active and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard.index"))

        flash("Неверный логин или пароль", "danger")

    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
