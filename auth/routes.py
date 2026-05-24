from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        if not username or not email or not password:
            flash("请填写所有字段", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(username=username).first():
            flash("用户名已存在", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("邮箱已注册", "error")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("密码至少6位", "error")
            return render_template("auth/register.html")

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("注册成功，请登录", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash("用户名或密码错误", "error")
            return render_template("auth/login.html")

        login_user(user)
        flash(f"欢迎回来，{user.username}！", "success")
        return redirect(url_for("home"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("已退出登录", "success")
    return redirect(url_for("auth.login"))
