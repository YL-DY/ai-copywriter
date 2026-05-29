from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
import requests
import hashlib
import os
from datetime import date

from models import db, User, History
from auth.routes import auth_bp

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "xiaohongshu-secret-key-2024")
# Railway 部署用 PostgreSQL，本地开发用 SQLite
database_url = os.environ.get("DATABASE_URL", "sqlite:///xiaohongshu.db")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "请先登录"


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None


app.register_blueprint(auth_bp)

# ===== 首次请求时创建数据库表 =====
_db_initialized = False

@app.before_request
def ensure_db():
    global _db_initialized
    if not _db_initialized:
        import sqlite3
        db_path = "instance/xiaohongshu.db"
        os.makedirs("instance", exist_ok=True)
        db.create_all()
        # 检查表是否存在
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            table_exists = cursor.fetchone() is not None
            conn.close()
            if not table_exists:
                # 表不存在，完全重建
                db.create_all()
        except Exception:
            db.create_all()
        try:
            from sqlalchemy import inspect, text as _text
            ins = inspect(db.engine)
            columns = [c["name"] for c in ins.get_columns("users")]
            if "daily_count" not in columns:
                db.session.execute(_text("ALTER TABLE users ADD COLUMN daily_count INTEGER DEFAULT 0"))
            if "daily_date" not in columns:
                db.session.execute(_text("ALTER TABLE users ADD COLUMN daily_date VARCHAR(10) DEFAULT ''"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        _db_initialized = True

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-929e447310024be5bec2a1587f2c414f")


# ========== Prompt 模板库 ==========
STYLE_PROMPTS = {
    "爆款风": """请帮我写一篇小红书爆款文案。

产品：{product}

要求：
1. 标题夸张吸睛
2. 情绪强烈
3. 带很多emoji
4. 容易引发点赞评论
5. 像热门博主语气
{extra}""",

    "高级感": """请帮我写一篇高级感小红书文案。

产品：{product}

要求：
1. 文案精致
2. 有氛围感
3. 像高端生活方式博主
4. 用词高级
5. 带适量emoji
{extra}""",

    "带货风": """请帮我写一篇带货型小红书文案。

产品：{product}

要求：
1. 强调产品优点
2. 有购买欲
3. 有种草感
4. 引导下单
5. 像专业博主推荐
{extra}""",

    "情绪风": """请帮我写一篇情绪感强的小红书文案。

产品：{product}

要求：
1. 有情绪表达
2. 容易共鸣
3. 像真实生活分享
4. 有故事感
5. 带emoji
{extra}""",

    "搞笑风": """请帮我写一篇搞笑风格小红书文案。

产品：{product}

要求：
1. 幽默搞笑
2. 网络热梗
3. 有段子感
4. 轻松有趣
5. 带emoji
{extra}""",

    "干货教程": """请帮我写一篇干货型小红书教程。

产品：{product}

要求：
1. 教学性强
2. 步骤清晰
3. 实用价值高
4. 像专业领域博主
5. 带适量emoji
{extra}""",

    "测评对比": """请帮我写一篇测评对比型小红书文案。

产品：{product}

要求：
1. 客观对比
2. 优缺点分析
3. 真实使用感受
4. 有说服力
5. 像真实用户测评
{extra}""",
}

STYLE_ICONS = {
    "爆款风": "🔥",
    "高级感": "✨",
    "带货风": "🛍️",
    "情绪风": "💭",
    "搞笑风": "😂",
    "干货教程": "📖",
    "测评对比": "⚖️",
}


def estimate_tokens(text):
    return len(text)


def generate_prompt(product, style, custom_prompt="", word_count=""):
    base = STYLE_PROMPTS.get(style, STYLE_PROMPTS["爆款风"])

    extra_parts = []
    if custom_prompt:
        extra_parts.append(f"\n额外要求：\n{custom_prompt}")
    if word_count:
        extra_parts.append(f"\n字数要求：请控制在 {word_count} 字左右")

    extra = "\n".join(extra_parts)
    return base.format(product=product, extra=extra)


@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    result = ""
    result_tokens = 0
    reuse_product = ""
    reuse_style = ""
    reuse_custom_prompt = ""
    reuse_word_count = ""

    if request.method == "POST":
        product = request.form["product"]
        style = request.form["style"]
        reuse_product = product
        reuse_style = style
        custom_prompt = request.form.get("custom_prompt", "").strip()
        word_count = request.form.get("word_count", "").strip()
        reuse_custom_prompt = custom_prompt
        reuse_word_count = word_count

        # 每日限额检查
        today = date.today().isoformat()
        if current_user.daily_date != today:
            current_user.daily_count = 0
            current_user.daily_date = today

        if not current_user.is_premium and current_user.daily_count >= 10:
            flash("今日免费次数已用完（每日 10 次），明天再来吧", "error")
            return render_template("home.html", result="", result_tokens=0,
                                   reuse_product=reuse_product, reuse_style=reuse_style,
                                   reuse_custom_prompt=reuse_custom_prompt, reuse_word_count=reuse_word_count)

        prompt = generate_prompt(product, style, custom_prompt, word_count)
        prompt_tokens = estimate_tokens(prompt)

        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            resp_data = response.json()

            if "choices" not in resp_data:
                flash(f"API 调用失败：{resp_data}", "error")
                return render_template("home.html", result="", result_tokens=0,
                                       reuse_product=reuse_product, reuse_style=reuse_style,
                                       reuse_custom_prompt=reuse_custom_prompt, reuse_word_count=reuse_word_count)

            result = resp_data["choices"][0]["message"]["content"]
            output_tokens = estimate_tokens(result)
            result_tokens = prompt_tokens + output_tokens

            history = History(
                user_id=current_user.id,
                product=product,
                style=style,
                prompt=prompt,
                result=result,
                tokens_used=result_tokens,
            )
            db.session.add(history)
            current_user.total_tokens += result_tokens
            current_user.daily_count += 1
            db.session.commit()

            flash(f"生成成功！消耗约 {result_tokens} tokens", "success")

        except requests.exceptions.Timeout:
            flash("API 请求超时，请稍后重试", "error")
        except Exception as e:
            flash(f"生成失败：{str(e)}", "error")

    return render_template("home.html", result=result, result_tokens=result_tokens,
                           reuse_product=reuse_product, reuse_style=reuse_style,
                           reuse_custom_prompt=reuse_custom_prompt, reuse_word_count=reuse_word_count)


@app.route("/history")
@login_required
def history():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()

    query = History.query.filter_by(user_id=current_user.id)
    if search:
        query = query.filter(History.product.contains(search))

    pagination = query.order_by(History.created_at.desc())\
        .paginate(page=page, per_page=10, error_out=False)

    return render_template("history.html", pagination=pagination, search=search)


@app.route("/history/delete/<int:history_id>", methods=["POST"])
@login_required
def delete_history(history_id):
    item = History.query.get_or_404(history_id)
    if item.user_id != current_user.id:
        flash("无权限删除", "error")
        return redirect(url_for("history"))
    db.session.delete(item)
    db.session.commit()
    flash("已删除", "success")
    return redirect(url_for("history"))


@app.route("/history/regenerate/<int:history_id>")
@login_required
def regenerate(history_id):
    item = History.query.get_or_404(history_id)
    if item.user_id != current_user.id:
        flash("无权限", "error")
        return redirect(url_for("history"))
    return render_template("home.html",
                           result="",
                           reuse_product=item.product,
                           reuse_style=item.style)


@app.route("/profile")
@login_required
def profile():
    total_count = History.query.filter_by(user_id=current_user.id).count()
    total_tokens_used = db.session.query(db.func.sum(History.tokens_used))\
        .filter(History.user_id == current_user.id).scalar() or 0
    return render_template("profile.html", total_count=total_count,
                           total_tokens_used=total_tokens_used)


@app.context_processor
def inject_globals():
    if current_user.is_authenticated:
        remaining = current_user.tokens_remaining
        today = date.today().isoformat()
        if current_user.daily_date != today:
            daily_used = 0
        else:
            daily_used = current_user.daily_count
        daily_remaining = max(0, 10 - daily_used)
        return dict(user_token_remaining=remaining,
                    daily_remaining=daily_remaining,
                    style_icons=STYLE_ICONS,
                    style_list=list(STYLE_PROMPTS.keys()))
    return dict(user_token_remaining=0,
                daily_remaining=10,
                style_icons=STYLE_ICONS,
                style_list=list(STYLE_PROMPTS.keys()))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
