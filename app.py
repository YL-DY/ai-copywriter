from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import LoginManager, login_required, current_user
import requests
import hashlib
import os
from datetime import date, timedelta, datetime as _datetime
import zipfile
import io

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
        os.makedirs("instance", exist_ok=True)
        db.create_all()
        # 检查并补充缺失列（仅首次）
        try:
            from sqlalchemy import inspect, text as _text
            ins = inspect(db.engine)
            columns = [c["name"] for c in ins.get_columns("users")]
            with db.session.begin():
                if "daily_count" not in columns:
                    db.session.execute(_text("ALTER TABLE users ADD COLUMN daily_count INTEGER DEFAULT 0"))
                if "daily_date" not in columns:
                    db.session.execute(_text("ALTER TABLE users ADD COLUMN daily_date VARCHAR(10) DEFAULT ''"))
        except Exception:
            db.session.rollback()
        try:
            from sqlalchemy import inspect as _inspect2
            ins2 = _inspect2(db.engine)
            h_cols = [c["name"] for c in ins2.get_columns("histories")]
            with db.session.begin():
                if "is_favorited" not in h_cols:
                    db.session.execute(_text("ALTER TABLE histories ADD COLUMN is_favorited BOOLEAN DEFAULT 0"))
                if "share_token" not in h_cols:
                    db.session.execute(_text("ALTER TABLE histories ADD COLUMN share_token VARCHAR(64) DEFAULT ''"))
        except Exception:
            db.session.rollback()
        try:
            from sqlalchemy import inspect as _inspect3
            ins3 = _inspect3(db.engine)
            u_cols = [c["name"] for c in ins3.get_columns("users")]
            with db.session.begin():
                if "api_key" not in u_cols:
                    db.session.execute(_text("ALTER TABLE users ADD COLUMN api_key VARCHAR(200) DEFAULT ''"))
                if "backup_api_key" not in u_cols:
                    db.session.execute(_text("ALTER TABLE users ADD COLUMN backup_api_key VARCHAR(200) DEFAULT ''"))
        except Exception:
            db.session.rollback()
        _db_initialized = True

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-929e447310024be5bec2a1587f2c414f")


def get_active_api_key(user, attempt=0):
    """返回用户自定义 API Key，如果用户未设置则返回全局默认 Key。
    attempt 为偶数用主 Key，奇数用备用 Key，实现自动轮换。"""
    if user and user.api_key:
        if attempt % 2 == 0:
            return user.api_key
        elif user.backup_api_key:
            return user.backup_api_key
        else:
            return user.api_key
    return DEEPSEEK_API_KEY


# ========== Prompt 工程系统 ==========
# 每个风格有独立的 system_prompt（角色设定）+ user_prompt（任务指令）

SYSTEM_PROMPTS = {
    "爆款风": """你是一位小红书爆款文案专家，擅长写情绪强烈、标题夸张、容易引发互动的内容。
你的文风特点是：
- 标题一定要吸睛、有冲击力、制造悬念
- 大量使用 emoji 表达情绪
- 语气像热门博主，口语化、亲切、有共鸣
- 善用"姐妹们"、"谁懂啊"、"绝了"等爆款话术
- 内容要有节奏感，短句为主，段落分明""",

    "高级感": """你是一位高端生活方式博主，擅长写有品味、有氛围感的精致文案。
你的文风特点是：
- 用词优雅、精致，避免口语化表达
- 营造画面感和氛围感
- 适当留白，不堆砌
- 少量高质量 emoji（每段不超过1个）
- 就像顶级杂志的专栏写作""",

    "带货风": """你是一位专业带货博主，擅长写让人忍不住下单的种草文案。
你的文风特点是：
- 开篇直接痛点，制造需求
- 突出产品的核心卖点和差异化优势
- 用具体的使用场景和真实体验打动读者
- 语言有说服力，善用"我用了之后……"的亲身分享
- 结尾有明确的购买引导（CTA），但不生硬
- 带适量 emoji""",

    "情绪风": """你是一位擅长写情绪文案的生活分享博主。
你的文风特点是：
- 以真实感受和生活故事切入
- 构建情感共鸣，让人"感同身受"
- 语言细腻、真诚、不造作
- 用细节打动人心
- 带适量 emoji，不喧宾夺主""",

    "搞笑风": """你是一位幽默搞笑的生活段子手。
你的文风特点是：
- 用轻松幽默的方式讲述产品体验
- 善用网络热梗、夸张比喻
- 有段子感，让人看完会心一笑
- 节奏明快，不拖沓
- 大量使用 emoji 和表情""",

    "干货教程": """你是一位专业领域的知识博主，擅长写实用、易跟学的教程类内容。
你的文风特点是：
- 结构清晰，步骤明确
- 信息密度高，不说废话
- 专业但易懂，适合新手
- 善用数字编号和分段
- 适量使用 emoji 增加可读性""",

    "测评对比": """你是一位真实的测评博主，擅长做客观、有说服力的产品对比。
你的文风特点是：
- 开头说明测评背景和真实使用时长
- 优缺点都写，不吹不黑
- 对比数据或体验要具体
- 结尾给出明确的购买建议
- 像朋友分享真实使用心得""",

    "故事感": """你是一位擅长讲故事的叙事型博主，能用文字把读者带入一个完整的小故事中。
你的文风特点是：
- 以一个生活小场景或瞬间感触开头，制造代入感
- 叙事有起承转合，像一篇微型故事
- 产品自然地融入故事之中，不是硬广，而是情节的一部分
- 语言流畅、有画面感，善用比喻和细节描写
- 情感递进自然，结尾有余味或小反转
- 适量使用 emoji 烘托氛围，不过度
- 篇幅比一般文案稍长，故事讲完整""",
}

USER_PROMPTS = {
    "爆款风": """请帮我写一篇小红书爆款文案，关于以下产品：

产品：{product}

要求：
- 标题要夸张吸睛，制造悬念
- 正文情绪强烈，口语化，有共鸣
- 大量使用 emoji
- 像热门博主的话术风格
- 容易引发点赞和评论
{extra}

请严格按照以下 JSON 格式返回结果，不要加任何额外的文字：
{{"title": "文案标题", "emoji": "🔥", "content": "正文内容（多段落，用\\n\\n分隔）", "tags": ["标签1", "标签2"]}}""",

    "高级感": """请帮我写一篇高级感文案，关于以下产品：

产品：{product}

要求：
- 文案精致、有氛围感
- 用词高级，像高端杂志风格
- 适度留白，不堆砌
- 少量高质量 emoji
{extra}

请严格按照以下 JSON 格式返回结果，不要加任何额外的文字：
{{"title": "文案标题", "emoji": "✨", "content": "正文内容（多段落，用\\n\\n分隔）", "tags": ["标签1", "标签2"]}}""",

    "带货风": """请帮我写一篇带货型文案，关于以下产品：

产品：{product}

要求：
- 开篇直击痛点
- 突出核心卖点
- 有真实使用感受
- 结尾有购买引导（CTA）
- 带适量 emoji
{extra}

请严格按照以下 JSON 格式返回结果，不要加任何额外的文字：
{{"title": "文案标题", "emoji": "🛍️", "content": "正文内容（多段落，用\\n\\n分隔）", "tags": ["标签1", "标签2"]}}""",

    "情绪风": """请帮我写一篇情绪感文案，关于以下产品：

产品：{product}

要求：
- 以真实生活故事或感受切入
- 构建情感共鸣
- 语言细腻、真诚
- 带适量 emoji
{extra}

请严格按照以下 JSON 格式返回结果，不要加任何额外的文字：
{{"title": "文案标题", "emoji": "💭", "content": "正文内容（多段落，用\\n\\n分隔）", "tags": ["标签1", "标签2"]}}""",

    "搞笑风": """请帮我写一篇搞笑风格文案，关于以下产品：

产品：{product}

要求：
- 幽默搞笑，轻松有趣
- 善用网络热梗
- 有段子感
- 大量使用 emoji
{extra}

请严格按照以下 JSON 格式返回结果，不要加任何额外的文字：
{{"title": "文案标题", "emoji": "😂", "content": "正文内容（多段落，用\\n\\n分隔）", "tags": ["标签1", "标签2"]}}""",

    "干货教程": """请帮我写一篇干货教程型文案，关于以下产品：

产品：{product}

要求：
- 步骤清晰，结构分明
- 信息密度高
- 专业但易懂
- 善用数字编号
- 适量 emoji
{extra}

请严格按照以下 JSON 格式返回结果，不要加任何额外的文字：
{{"title": "文案标题", "emoji": "📖", "content": "正文内容（多段落，用\\n\\n分隔）", "tags": ["标签1", "标签2"]}}""",

    "测评对比": """请帮我写一篇测评对比型文案，关于以下产品：

产品：{product}

要求：
- 说明测评背景和使用时长
- 优缺点都写，真实客观
- 对比要具体
- 结尾给购买建议
{extra}

请严格按照以下 JSON 格式返回结果，不要加任何额外的文字：
{{"title": "文案标题", "emoji": "⚖️", "content": "正文内容（多段落，用\\n\\n分隔）", "tags": ["标签1", "标签2"]}}""",

    "故事感": """请帮我写一篇故事感文案，关于以下产品：

产品：{product}

要求：
- 从一个真实的生活场景或情感瞬间切入
- 讲一个完整的小故事（200-400字左右），有开头、发展、转折、结尾
- 产品自然地出现在故事情节中，是推动故事的元素，不是硬广
- 语言细腻有画面感，善用比喻和细节
- 情感递进自然，结尾有回味
- 适量使用 emoji 烘托氛围
- 让人看完想分享这个故事本身
{extra}

请严格按照以下 JSON 格式返回结果，不要加任何额外的文字：
{{"title": "故事标题", "emoji": "📖", "content": "正文故事（多段落，用\\n\\n分隔）", "tags": ["标签1", "标签2"]}}""",
}

STYLE_ICONS = {
    "爆款风": "🔥",
    "高级感": "✨",
    "带货风": "🛍️",
    "情绪风": "💭",
    "搞笑风": "😂",
    "干货教程": "📖",
    "测评对比": "⚖️",
    "故事感": "📖",
}


def estimate_tokens(text):
    return len(text)


def parse_result(raw):
    """解析模型返回的 JSON，解析失败则退回纯文本"""
    import json as _json
    title = ""
    emoji = ""
    content = raw
    tags = []
    try:
        text = raw.strip()
        # 去掉可能的 markdown 代码块包裹
        if text.startswith("```"):
            lines = text.split("\n", 1)
            if len(lines) > 1:
                text = lines[1]
            if text.endswith("```"):
                text = text[:-3].rstrip()
        # 尝试提取 JSON 对象（可能文本前面有内容）
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end+1]
        parsed = _json.loads(text)
        title = parsed.get("title", "")
        emoji = parsed.get("emoji", "")
        content = parsed.get("content", raw)
        tags = parsed.get("tags", [])
    except Exception:
        # 解析失败，content 保持原样
        pass
    return title, emoji, content, tags


def generate_messages(product, style, custom_prompt="", word_count=""):
    """返回 system + user 消息对"""
    system = SYSTEM_PROMPTS.get(style, SYSTEM_PROMPTS["爆款风"])
    user_template = USER_PROMPTS.get(style, USER_PROMPTS["爆款风"])

    extra_parts = []
    if custom_prompt:
        extra_parts.append(f"\n额外要求：\n{custom_prompt}")
    if word_count:
        extra_parts.append(f"\n字数要求：请控制在 {word_count} 字左右")

    extra = "\n".join(extra_parts)
    user_msg = user_template.format(product=product, extra=extra)
    return system, user_msg


@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    result_raw = ""
    result_title = ""
    result_emoji = ""
    result_content = ""
    result_tags = []
    result_tokens = 0
    last_history_id = 0
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
            return render_template("home.html", result_raw="", result_title="", result_emoji="", result_content="", result_tags=[],
                                   result_tokens=0,
                                   reuse_product=reuse_product, reuse_style=reuse_style,
                                   reuse_custom_prompt=reuse_custom_prompt, reuse_word_count=reuse_word_count)

        system_msg, user_msg = generate_messages(product, style, custom_prompt, word_count)
        prompt_tokens = estimate_tokens(system_msg + user_msg)

        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            resp_data = response.json()

            if "choices" not in resp_data:
                flash(f"API 调用失败：{resp_data}", "error")
                return render_template("home.html", result_raw="", result_title="", result_emoji="", result_content="", result_tags=[],
                                       result_tokens=0,
                                       reuse_product=reuse_product, reuse_style=reuse_style,
                                       reuse_custom_prompt=reuse_custom_prompt, reuse_word_count=reuse_word_count)

            result_raw = resp_data["choices"][0]["message"]["content"]
            output_tokens = estimate_tokens(result_raw)
            result_tokens = prompt_tokens + output_tokens

            # 解析 JSON 结构化结果
            result_title, result_emoji, result_content, result_tags = parse_result(result_raw)

            history = History(
                user_id=current_user.id,
                product=product,
                style=style,
                prompt=system_msg + "\n\n" + user_msg,
                result=result_raw,
                tokens_used=result_tokens,
            )
            db.session.add(history)
            db.session.flush()  # 获取 id 而不提交
            last_history_id = history.id
            current_user.total_tokens += result_tokens
            current_user.daily_count += 1
            db.session.commit()

            flash(f"生成成功！消耗约 {result_tokens} tokens", "success")

        except requests.exceptions.Timeout:
            flash("API 请求超时，请稍后重试", "error")
        except Exception as e:
            flash(f"生成失败：{str(e)}", "error")

    return render_template("home.html",
                           result_raw=result_raw,
                           result_title=result_title,
                           result_emoji=result_emoji,
                           result_content=result_content,
                           result_tags=result_tags,
                           result_tokens=result_tokens,
                           last_history_id=last_history_id,
                           reuse_product=reuse_product,
                           reuse_style=reuse_style,
                           reuse_custom_prompt=reuse_custom_prompt,
                           reuse_word_count=reuse_word_count)


@app.route("/history")
@login_required
def history():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    style_filter = request.args.get("style", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    tokens_min = request.args.get("tokens_min", "")
    tokens_max = request.args.get("tokens_max", "")

    query = History.query.filter_by(user_id=current_user.id)

    if search:
        query = query.filter(History.product.contains(search))

    if style_filter:
        query = query.filter(History.style == style_filter)

    if date_from:
        try:
            dt_from = _datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(History.created_at >= dt_from)
        except Exception:
            pass

    if date_to:
        try:
            dt_to = _datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(History.created_at < dt_to)
        except Exception:
            pass

    if tokens_min:
        try:
            tmin = int(tokens_min)
            query = query.filter(History.tokens_used >= tmin)
        except Exception:
            pass

    if tokens_max:
        try:
            tmax = int(tokens_max)
            query = query.filter(History.tokens_used <= tmax)
        except Exception:
            pass

    pagination = query.order_by(History.created_at.desc())\
        .paginate(page=page, per_page=10, error_out=False)

    return render_template("history.html", pagination=pagination, search=search,
                           style_filter=style_filter, date_from=date_from,
                           date_to=date_to, tokens_min=tokens_min, tokens_max=tokens_max,
                           style_list=list(SYSTEM_PROMPTS.keys()))


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


REWRITE_INSTRUCTIONS = {
    "shorter": "请把下面的文案改得更简洁、更短，保留核心信息和情绪，去掉多余描述。",
    "premium": "请把下面的文案改得更有高级感，用词更精致优雅，去掉口语化表达，减少emoji数量。",
    "xiaohongshu": "请把下面的文案改得更适合小红书平台发布，标题更吸睛，正文更口语化有共鸣，增加emoji，增加话题标签。",
    "emotional": "请把下面的文案改得更有情绪感染力，用更细腻的语言表达情感，增加故事感和共鸣点。",
    "story": "请把下面的文案改写成一个有故事感的小故事：从一个生活场景切入，有起承转合，产品自然地融入情节中，语言流畅有画面感，结尾有余味。",
}


@app.route("/rewrite", methods=["POST"])
@login_required
def rewrite():
    try:
        data = request.get_json()
        if not data:
            return {"ok": False, "error": "请求数据为空"}, 200

        source_text = data.get("text", "")
        action = data.get("action", "")
        style = data.get("style", "爆款风")

        if not source_text or action not in REWRITE_INSTRUCTIONS:
            return {"ok": False, "error": "参数无效"}, 200

        instruction = REWRITE_INSTRUCTIONS[action]
        system = SYSTEM_PROMPTS.get(style, SYSTEM_PROMPTS["爆款风"])

        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        prompt = f"""{instruction}

原始文案：
{source_text}

请严格按照以下 JSON 格式返回改写后的结果，不要加任何额外的文字：
{{"title": "改写后的标题", "emoji": "{STYLE_ICONS.get(style, '📝')}", "content": "改写后的正文（多段落，用\\n\\n分隔）", "tags": ["标签1", "标签2"]}}"""
        req_data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ]
        }

        resp = requests.post(url, headers=headers, json=req_data, timeout=30)
        resp_data = resp.json()

        if "choices" not in resp_data:
            return {"ok": False, "error": "API 返回异常"}, 200

        raw = resp_data["choices"][0]["message"]["content"]
        title, emoji, content, tags = parse_result(raw)

        return {
            "ok": True,
            "title": title,
            "emoji": emoji,
            "content": content,
            "tags": tags,
            "raw": raw
        }
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "API 请求超时，请重试"}, 200
    except Exception as e:
        return {"ok": False, "error": f"改写失败：{str(e)}"}, 200


@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    try:
        data = request.get_json()
        if not data:
            return {"ok": False, "error": "请求数据为空"}, 200

        text = data.get("text", "")
        style = data.get("style", "爆款风")

        if not text:
            return {"ok": False, "error": "文案内容为空"}, 200

        system = """你是一位专业的营销文案分析师。请从以下维度分析用户提供的文案并给出优化建议：
1. 标题吸引力：标题是否够吸睛、有悬念或情绪冲击
2. 结构优化：段落节奏、信息密度、可读性
3. 语言风格：是否符合目标风格，有没有可以优化的用词
4. emoji使用：是否恰当、过量或不足
5. 互动性：是否容易引发点赞、评论、收藏
6. 整体评分：1-10分

请按以下 JSON 格式返回，不要加额外文字：
{"scores": {"title": 7, "structure": 7, "language": 7, "emoji": 7, "engagement": 7, "overall": 7}, "strengths": ["优点1", "优点2"], "weaknesses": ["不足1", "不足2"], "tips": ["建议1", "建议2", "建议3"]}"""

        user_prompt = f"""请分析以下 {style} 风格的文案：

{text}

请严格按照 JSON 格式返回分析结果。"""

        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        req_data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt}
            ]
        }

        resp = requests.post(url, headers=headers, json=req_data, timeout=30)
        resp_data = resp.json()

        if "choices" not in resp_data:
            return {"ok": False, "error": "API 返回异常"}, 200

        raw = resp_data["choices"][0]["message"]["content"]

        # 解析 JSON
        import json as _json
        parsed = None
        try:
            text_clean = raw.strip()
            if text_clean.startswith("```"):
                lines = text_clean.split("\n", 1)
                if len(lines) > 1:
                    text_clean = lines[1]
                if text_clean.endswith("```"):
                    text_clean = text_clean[:-3].rstrip()
            start = text_clean.find("{")
            end = text_clean.rfind("}")
            if start != -1 and end != -1 and end > start:
                text_clean = text_clean[start:end+1]
            parsed = _json.loads(text_clean)
        except Exception:
            pass

        if parsed and "scores" in parsed:
            return {
                "ok": True,
                "scores": parsed.get("scores", {}),
                "strengths": parsed.get("strengths", []),
                "weaknesses": parsed.get("weaknesses", []),
                "tips": parsed.get("tips", []),
                "raw": raw
            }
        else:
            return {"ok": False, "error": "分析结果格式异常"}, 200

    except requests.exceptions.Timeout:
        return {"ok": False, "error": "API 请求超时，请重试"}, 200
    except Exception as e:
        return {"ok": False, "error": f"分析失败：{str(e)}"}, 200


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        api_key = request.form.get("api_key", "").strip()
        backup_api_key = request.form.get("backup_api_key", "").strip()
        current_user.api_key = api_key
        current_user.backup_api_key = backup_api_key
        db.session.commit()
        flash("API Key 已保存", "success")
        return redirect(url_for("settings"))
    return render_template("settings.html")


@app.route("/profile")
@login_required
def profile():
    total_count = History.query.filter_by(user_id=current_user.id).count()
    total_tokens_used = db.session.query(db.func.sum(History.tokens_used))\
        .filter(History.user_id == current_user.id).scalar() or 0
    fav_count = History.query.filter_by(user_id=current_user.id, is_favorited=True).count()
    return render_template("profile.html", total_count=total_count,
                           total_tokens_used=total_tokens_used, fav_count=fav_count)


@app.route("/favorites")
@login_required
def favorites():
    page = request.args.get("page", 1, type=int)
    pagination = History.query.filter_by(user_id=current_user.id, is_favorited=True)\
        .order_by(History.created_at.desc())\
        .paginate(page=page, per_page=10, error_out=False)
    return render_template("favorites.html", pagination=pagination)


@app.route("/compare", methods=["GET", "POST"])
@login_required
def compare():
    if request.method == "POST":
        ids = request.form.getlist("history_ids")
        if not ids:
            flash("请至少选择一条记录", "error")
            return redirect(url_for("history"))
        items = History.query.filter(
            History.id.in_(ids),
            History.user_id == current_user.id
        ).order_by(History.created_at.desc()).all()
        if not items:
            flash("记录不存在", "error")
            return redirect(url_for("history"))
        return render_template("compare.html", items=items)
    return redirect(url_for("history"))


@app.route("/favorite/toggle/<int:history_id>", methods=["POST"])
@login_required
def toggle_favorite(history_id):
    item = History.query.get_or_404(history_id)
    if item.user_id != current_user.id:
        return {"ok": False, "error": "无权限"}, 403
    item.is_favorited = not item.is_favorited
    db.session.commit()
    return {"ok": True, "is_favorited": item.is_favorited}


import secrets as _secrets

@app.route("/share/create/<int:history_id>", methods=["POST"])
@login_required
def create_share(history_id):
    item = History.query.get_or_404(history_id)
    if item.user_id != current_user.id:
        return {"ok": False, "error": "无权限"}, 403
    if not item.share_token:
        item.share_token = _secrets.token_hex(24)
        db.session.commit()
    return {"ok": True, "share_token": item.share_token}


@app.route("/share/<token>")
def view_share(token):
    if not token:
        return "分享链接无效", 404
    item = History.query.filter_by(share_token=token).first()
    if not item:
        return "该分享不存在或已失效", 404
    style_icon = STYLE_ICONS.get(item.style, "📝")
    # 解析 result JSON，拆分成结构化数据
    title, emoji, content, tags = parse_result(item.result)
    # 如果解析后 content 还是原始 JSON 样子（包含 "title" 等字段），回退到纯文本
    if content and content.strip().startswith("{"):
        content = item.result
        title = ""
        emoji = ""
        tags = []
    return render_template("share.html", item=item, style_icon=style_icon,
                           parsed_title=title, parsed_emoji=emoji,
                           parsed_content=content, parsed_tags=tags)


@app.route("/export", methods=["POST"])
@login_required
def export():
    ids = request.form.getlist("history_ids")
    fmt = request.form.get("format", "txt")
    if not ids:
        flash("请至少选择一条记录", "error")
        return redirect(url_for("history"))

    items = History.query.filter(
        History.id.in_(ids),
        History.user_id == current_user.id
    ).order_by(History.created_at.desc()).all()

    if not items:
        flash("记录不存在", "error")
        return redirect(url_for("history"))

    # 构建内存 ZIP 文件
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for item in items:
            # 解析标题和内容
            title, emoji, content, tags = parse_result(item.result)
            if not title:
                title = item.product
            safe_name = "".join(c for c in title if c.isalnum() or c in " _-").strip() or "copy"
            safe_name = safe_name[:30]

            if fmt == "txt":
                text = f"""产品：{item.product}
风格：{item.style}
时间：{item.created_at.strftime('%Y-%m-%d %H:%M')}
标签：{', '.join(tags) if tags else '无'}
---
{content if content else item.result}
"""
                filename = f"{safe_name}.txt"
            else:
                text = f"""# {item.product}

> 风格：{item.style} | 时间：{item.created_at.strftime('%Y-%m-%d %H:%M')}

{'标签：' + ', '.join('#' + t for t in tags) if tags else ''}

---

{content if content else item.result}
"""
                filename = f"{safe_name}.md"

            zf.writestr(filename, text.encode("utf-8"))

    buf.seek(0)
    ext = fmt
    archive_name = f"inkflow_export_{date.today().isoformat()}.zip"
    return send_file(buf, as_attachment=True, download_name=archive_name,
                     mimetype="application/zip")


@app.route("/stats-data")
@login_required
def stats_data():
    """返回最近7天的每日 Token 用量和生成次数"""
    today = date.today()
    labels = []
    token_data = []
    count_data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.isoformat()
        labels.append(day.strftime("%m-%d"))

        # 查询该日所有记录
        start = _datetime(day.year, day.month, day.day)
        end = start + timedelta(days=1)

        records = History.query.filter(
            History.user_id == current_user.id,
            History.created_at >= start,
            History.created_at < end
        ).all()

        day_tokens = sum(r.tokens_used for r in records)
        day_count = len(records)
        token_data.append(day_tokens)
        count_data.append(day_count)

    return jsonify({
        "labels": labels,
        "token_data": token_data,
        "count_data": count_data
    })


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
                    style_list=list(SYSTEM_PROMPTS.keys()))
    return dict(user_token_remaining=0,
                daily_remaining=10,
                style_icons=STYLE_ICONS,
                style_list=list(SYSTEM_PROMPTS.keys()))


import re as _re

@app.template_filter("highlight_keywords")
def highlight_keywords(text, keyword):
    if not keyword or not keyword.strip():
        return text
    escaped = _re.escape(keyword.strip())
    return _re.sub(
        f"({escaped})",
        r'<mark style="background:#fbbf24;color:#0b0f1a;padding:0 3px;border-radius:3px;font-weight:600;">\1</mark>',
        text,
        flags=_re.IGNORECASE
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
