from flask import Flask, render_template
from flask_login import LoginManager
from models import db, User


def create_app():
    app = Flask(__name__)
    app.config.from_object("config")

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Войдите, чтобы получить доступ к этой странице"
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from auth.routes import bp as auth_bp
    from dashboard.routes import bp as dashboard_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    # Регистрируем has_permission как глобальную функцию в Jinja2
    from access.decorators import has_permission
    app.jinja_env.globals['has_permission'] = has_permission

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
