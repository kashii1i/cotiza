from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin:
        return render_template("dashboard/admin_dashboard.html")
    return render_template("dashboard/seller_dashboard.html")


@main_bp.route("/health")
def health():
    return {"status": "ok"}
