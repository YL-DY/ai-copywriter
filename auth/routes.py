from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
import re
import os as _os
import requests as http_requests
import urllib.parse

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# === 微信开放平台配置 ===
WECHAT_APP_ID = _os.environ.get("WECHAT_APP_ID", "wxa21a1be58207509c")
WECHAT_APP_SECRET = _os.environ.get("WECHAT_APP_SECRET", "6d63cafe7a1914052ca5679381869db7")
WECHAT_REDIRECT_URI = _os.environ.get("WECHAT_REDIRECT_URI", "")

# === 敏感词列表 ===
SENSITIVE_WORDS = [
    "杀人", "自杀", "贩毒", "吸毒", "枪杀", "砍人", "爆炸", "恐怖", "暴力",
    "色情", "裸聊", "裸照", "约炮", "嫖娼", "卖淫", "三级片", "成人片", "AV",
    "激情", "露点", "情色", "淫秽", "黄色",
    "枪支", "弹药", "毒品", "冰毒", "海洛因", "摇头丸", "迷药",
    "贩卖器官", "走私", "赌博",
]


def check_sensitive(text):
    """检查文本是否包含敏感词，返回 (is_clean, matched_word)"""
    if not text:
        return True, None
    text_lower = text.lower()
    for word in SENSITIVE_WORDS:
        if word in text_lower or word in text:
            return False, word
    return True, None


@auth_bp.route("/wechat/login")
def wechat_login():
    """跳转到微信扫码页"""
    if not WECHAT_APP_ID:
        return '{"ok": false, "error": "\u5fae\u4fe1\u767b\u5f55\u672a\u914d\u7f6e"}', 503
    state = _os.urandom(16).hex()
    session["wechat_state"] = state
    cb = WECHAT_REDIRECT_URI or (request.host_url.rstrip("/") + "/auth/wechat/callback")
    cb_enc = urllib.parse.quote(cb)
    wechat_url = (
        "https://open.weixin.qq.com/connect/qrconnect"
        "?appid=" + WECHAT_APP_ID +
        "&redirect_uri=" + cb_enc +
        "&response_type=code"
        "&scope=snsapi_login"
        "&state=" + state +
        "#wechat_redirect"
    )
    return redirect(wechat_url)


@auth_bp.route("/wechat/callback")
def wechat_callback():
    """微信回调处理"""
    code = request.args.get("code", "")
    state = request.args.get("state", "")

    saved_state = session.pop("wechat_state", "")
    if state != saved_state and saved_state:
        flash("\u9a8c\u8bc1\u5931\u8d25\uff0c\u8bf7\u91cd\u8bd5", "error")
        return redirect(url_for("auth.login"))

    if not code:
        flash("\u5fae\u4fe1\u767b\u5f55\u5931\u8d25\uff0c\u672a\u83b7\u53d6\u5230\u6388\u6743\u7801", "error")
        return redirect(url_for("auth.login"))

    # 1. 用 code 换取 access_token
    token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"
    try:
        resp = http_requests.get(token_url, params={
            "appid": WECHAT_APP_ID,
            "secret": WECHAT_APP_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        }, timeout=10)
        token_data = resp.json()
    except Exception as e:
        flash(f"\u5fae\u4fe1\u767b\u5f55\u7f51\u7edc\u9519\u8bef: {str(e)}", "error")
        return redirect(url_for("auth.login"))

    if "access_token" not in token_data:
        error_msg = token_data.get("errmsg", "\u672a\u77e5\u9519\u8bef")
        flash(f"\u5fae\u4fe1\u6388\u6743\u5931\u8d25: {error_msg}", "error")
        return redirect(url_for("auth.login"))

    access_token = token_data["access_token"]
    openid = token_data["openid"]
    unionid = token_data.get("unionid", "")

    # 2. 获取用户信息
    userinfo_url = "https://api.weixin.qq.com/sns/userinfo"
    try:
        resp2 = http_requests.get(userinfo_url, params={
            "access_token": access_token,
            "openid": openid,
        }, timeout=10)
        user_info = resp2.json()
    except Exception as e:
        flash(f"\u83b7\u53d6\u7528\u6237\u4fe1\u606f\u5931\u8d25: {str(e)}", "error")
        return redirect(url_for("auth.login"))

    if "nickname" not in user_info:
        flash("\u83b7\u53d6\u5fae\u4fe1\u7528\u6237\u4fe1\u606f\u5931\u8d25", "error")
        return redirect(url_for("auth.login"))

    nickname = user_info.get("nickname", "\u5fae\u4fe1\u7528\u6237")
    avatar = user_info.get("headimgurl", "")

    # 3. 敏感词检查
    clean, matched = check_sensitive(nickname)
    if not clean:
        flash(f"\u6635\u79f0\u5305\u542b\u654f\u611f\u5185\u5bb9\u300c{matched}\u300d\uff0c\u8bf7\u4fee\u6539\u5fae\u4fe1\u6635\u79f0\u540e\u518d\u8bd5", "error")
        return redirect(url_for("auth.login"))

    # 4. 查找或创建用户
    user = User.query.filter_by(wechat_openid=openid).first()
    if not user:
        base_username = f"wx_{openid[:8]}"
        username = base_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1

        user = User(
            username=username,
            email=f"{openid}@wechat.inkflow",
            password_hash="",
            wechat_openid=openid,
            wechat_unionid=unionid,
            nickname=nickname,
            avatar_url=avatar,
        )
        db.session.add(user)
        db.session.commit()
    else:
        if nickname and nickname != user.nickname:
            clean2, _ = check_sensitive(nickname)
            if clean2:
                user.nickname = nickname
        if avatar:
            user.avatar_url = avatar
        db.session.commit()

    login_user(user)
    flash(f"\u5fae\u4fe1\u767b\u5f55\u6210\u529f\uff0c\u6b22\u8fce {nickname}\uff01", "success")
    return redirect(url_for("home"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        if not username or not email or not password:
            flash("\u8bf7\u586b\u5199\u6240\u6709\u5b57\u6bb5", "error")
            return render_template("auth/register.html")

        # 敏感词检查
        clean, matched = check_sensitive(username)
        if not clean:
            flash(f"\u7528\u6237\u540d\u5305\u542b\u654f\u611f\u5185\u5bb9\u300c{matched}\u300d", "error")
            return render_template("auth/register.html")

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash("\u90ae\u7bb1\u683c\u5f0f\u4e0d\u6b63\u786e", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(username=username).first():
            flash("\u7528\u6237\u540d\u5df2\u5b58\u5728", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("\u90ae\u7bb1\u5df2\u6ce8\u518c", "error")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("\u5bc6\u7801\u81f3\u5c116\u4f4d", "error")
            return render_template("auth/register.html")

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("\u6ce8\u518c\u6210\u529f\uff0c\u8bf7\u767b\u5f55", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash("\u7528\u6237\u540d\u6216\u5bc6\u7801\u9519\u8bef", "error")
            return render_template("auth/login.html")

        login_user(user)
        flash(f"\u6b22\u8fce\u56de\u6765\uff0c{user.username}\uff01", "success")
        return redirect(url_for("home"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("\u5df2\u9000\u51fa\u767b\u5f55", "success")
    return redirect(url_for("auth.login"))
