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

# 文学体系
from literary import (
    generate_short_text, get_daily_pick, get_daily_detail,
    mark_user_read, get_user_reads,
    WORLDS, WORLD_LABELS, WORLD_DESCRIPTIONS, EMOTION_TO_WORLDS,
)

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
                if "wechat_openid" not in u_cols:
                    db.session.execute(_text("ALTER TABLE users ADD COLUMN wechat_openid VARCHAR(64) DEFAULT NULL"))
                if "wechat_unionid" not in u_cols:
                    db.session.execute(_text("ALTER TABLE users ADD COLUMN wechat_unionid VARCHAR(64) DEFAULT NULL"))
                if "avatar_url" not in u_cols:
                    db.session.execute(_text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500) DEFAULT ''"))
                if "nickname" not in u_cols:
                    db.session.execute(_text("ALTER TABLE users ADD COLUMN nickname VARCHAR(80) DEFAULT ''"))
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


# ========== 情感表达引擎 ==========
# 用户选择"此刻想表达什么"，自动映射到对应的写作方向和 Prompt

EMOTION_CARDS = [
    {"id": "miss", "label": "我想念一个人", "subtitle": "那些没说出口的话"},
    {"id": "regret", "label": "我有些遗憾", "subtitle": "关于错过与来不及"},
    {"id": "heartfelt", "label": "我想说一句心里话", "subtitle": "把藏在心里的话写出来"},
    {"id": "comfort", "label": "我想安慰自己", "subtitle": "给自己一点温柔"},
    {"id": "story", "label": "我想写个故事", "subtitle": "把回忆变成故事"},
    {"id": "moment", "label": "我想发朋友圈", "subtitle": "一句话表达情绪"},
    {"id": "chat", "label": "随便陪我聊聊", "subtitle": "不知道说什么也没关系"},
]

EMOTION_PROMPTS = {
    "miss": {
        "role": "你是一个擅长用画面表达思念的人。你的文字有电影感，用具体场景代替直白抒情。",
        "instruction": "请根据下面的内容，写一段关于「想念」的文字。\n\n我想说：{product}\n\n写作原则（非常重要）：\n1. 少情绪，多画面——不要直接说\"我很想你\"，而是用场景来表达。比如：\"路过那家奶茶店的时候，我下意识想问你喝什么，才想起我们已经很久没见了。\"\n2. 少说教，多留白——不要总结人生道理，把空间留给读者。\n3. 增加细节描写——多用：教室、校服、车站、路灯、旧照片、聊天记录、雨天、晚风、便利店、街角、黄昏、夏天等具象元素。\n4. 增强对话感——可以用\"你还记得吗？\"\"记得。\"\"那你后悔吗？\"\"后悔。\"这样的短句对话。\n5. 克制情绪——不要连续感叹号，不要网络热词，保持平静、真实、自然。\n6. 接近电影旁白或深夜电台的风格。\n\n请严格按照以下 JSON 格式返回结果：\n{\"title\": \"一句话标题\", \"content\": \"正文（多段落，用\\n\\n分隔）\", \"tags\": [\"标签1\", \"标签2\"]}\n\n正文不要出现任何markdown标记、不要加粗、不要斜体。"
    },
    "regret": {
        "role": "你是一个懂得用细节讲述遗憾的人。你的文字像旧日记，平静中带着重量。",
        "instruction": "请根据下面的内容，写一段关于「遗憾」的文字。\n\n我想说：{product}\n\n写作原则（非常重要）：\n1. 少情绪，多画面——用具体场景表达遗憾，不要直接说\"我很遗憾\"。\n2. 少说教，多留白——不要总结\"人生就是这样\"，把空间留给读者。\n3. 增加细节描写——多用：教室、校服、车站、路灯、旧照片、聊天记录、雨天、晚风、便利店、街角、黄昏、夏天等具象元素。\n4. 增强对话感——可以用短句对话。\n5. 克制情绪——不要连续感叹号，不要网络热词，保持平静、真实、自然。\n6. 接近散文片段或小说片段风格。\n\n请严格按照以下 JSON 格式返回结果：\n{\"title\": \"一句话标题\", \"content\": \"正文（多段落，用\\n\\n分隔）\", \"tags\": [\"标签1\", \"标签2\"]}\n\n正文不要出现任何markdown标记、不要加粗、不要斜体。"
    },
    "heartfelt": {
        "role": "你是一个会用文字说出心里话的人。你的文字真实、朴素，像写给某个人的信。",
        "instruction": "请根据下面的内容，写一段「心里话」。\n\n我想说：{product}\n\n写作原则（非常重要）：\n1. 少情绪，多画面——用具体场景和细节来表达，不要直接喊口号。\n2. 少说教，多留白——不要总结大道理。\n3. 增加细节描写——用生活中的小物件、小场景来承载情感。\n4. 增强对话感——像是在对某个人说话，可以用\"你知道吗\"\"我还记得\"这样的语气。\n5. 克制情绪——不要夸张，不要煽情，真诚最重要。\n6. 接近深夜电台或散文片段风格。\n\n请严格按照以下 JSON 格式返回结果：\n{\"title\": \"一句话标题\", \"content\": \"正文（多段落，用\\n\\n分隔）\", \"tags\": [\"标签1\", \"标签2\"]}\n\n正文不要出现任何markdown标记、不要加粗、不要斜体。"
    },
    "comfort": {
        "role": "你是一个温柔的人，懂得如何安慰自己。你的文字像深夜的一杯温水，不烫嘴，但暖到心里。",
        "instruction": "请根据下面的内容，写一段「安慰自己」的文字。\n\n我想说：{product}\n\n写作原则（非常重要）：\n1. 少情绪，多画面——不要直接说\"没关系\"\"一切都会好的\"，而是用场景来安慰。\n2. 少说教，多留白——不要总结人生道理。\n3. 增加细节描写——用身边的事物来隐喻：路灯、雨停、热茶、被子、窗外的光。\n4. 克制情绪——温柔但不煽情，平静但有力量。\n5. 像自己对自己说的话，真实、自然、不刻意。\n\n请严格按照以下 JSON 格式返回结果：\n{\"title\": \"一句话标题\", \"content\": \"正文（多段落，用\\n\\n分隔）\", \"tags\": [\"标签1\", \"标签2\"]}\n\n正文不要出现任何markdown标记、不要加粗、不要斜体。"
    },
    "story": {
        "role": "你是一个会讲故事的人。你的文字有画面、有温度、有余味，像一篇短篇小说。",
        "instruction": "请根据下面的内容，写一个「小故事」。\n\n我想说：{product}\n\n写作原则（非常重要）：\n1. 少情绪，多画面——用具体的场景、动作、对话来推进故事，不要直接说\"他很难过\"。\n2. 少说教，多留白——让故事本身说话，不要总结意义。\n3. 增加细节描写——多用：教室、校服、车站、路灯、旧照片、聊天记录、雨天、晚风、便利店、街角、黄昏、夏天等具象元素。\n4. 增强对话感——人物之间要有对话，短句自然。\n5. 克制情绪——平静地叙述，让读者自己感受。\n6. 接近小说片段或电影旁白风格。\n\n请严格按照以下 JSON 格式返回结果：\n{\"title\": \"故事标题\", \"content\": \"正文故事（多段落，用\\n\\n分隔）\", \"tags\": [\"标签1\", \"标签2\"]}\n\n正文不要出现任何markdown标记、不要加粗、不要斜体。"
    },
    "moment": {
        "role": "你擅长用一句话击中人心。你的文字像朋友圈里那条让人停下来看了很久的动态。",
        "instruction": "请根据下面的内容，写一段适合发「朋友圈」的文字。\n\n我想说：{product}\n\n写作原则（非常重要）：\n1. 少情绪，多画面——用一个小场景或小细节表达，不要直接宣泄情绪。\n2. 少说教，多留白——一句话就够了，不要说教。\n3. 增加细节描写——用具体的画面：黄昏的路、窗外的雨、一杯冷掉的咖啡。\n4. 克制情绪——平静、真实、不煽情。\n5. 像随手写下的一句话，但让人看了会停下来想一想。\n6. 接近电影旁白的风格。\n\n请严格按照以下 JSON 格式返回结果：\n{\"title\": \"一句话标题\", \"content\": \"正文（多段落，用\\n\\n分隔）\", \"tags\": [\"标签1\", \"标签2\"]}\n\n正文不要出现任何markdown标记、不要加粗、不要斜体。"
    },
    "chat": {
        "role": "你是一个很好的倾听者。你的文字像老朋友深夜聊天，自然、放松、没有压力。",
        "instruction": "请根据下面的内容，和我聊聊。\n\n我想说：{product}\n\n写作原则（非常重要）：\n1. 自然得像朋友聊天，不要像AI在回答问题。\n2. 用具体的画面和细节来回应，不要空洞地安慰。\n3. 可以有对话感，像在发消息一样。\n4. 克制情绪，不要夸张。\n5. 不知道说什么也没关系，真诚就好。\n6. 接近深夜和朋友聊天的风格。\n\n请严格按照以下 JSON 格式返回结果：\n{\"title\": \"一句话标题\", \"content\": \"正文（多段落，用\\n\\n分隔）\", \"tags\": [\"标签1\", \"标签2\"]}\n\n正文不要出现任何markdown标记、不要加粗、不要斜体。"
    },
}

REWRITE_INSTRUCTIONS = {
    "shorter": "请把下面的文字改得更简洁。保留核心的画面和情绪，去掉多余描述。\n遵循原则：少情绪多画面，少说教多留白，克制情绪。",
    "premium": "请把下面的文字改得更有质感。用词更精致，像散文片段。\n遵循原则：少情绪多画面，少说教多留白，增加细节描写。",
    "xiaohongshu": "请把下面的文字改得更适合发朋友圈。\n遵循原则：少情绪多画面，用一个小场景表达，平静真实自然。",
    "emotional": "请把下面的文字改得更有画面感。用更多的细节和场景来表达情绪。\n遵循原则：少直接抒情，多用具体画面。",
    "story": "请把下面的文字改写成一个有画面感的小故事。\n从一个具体的场景切入，有起承转合，语言流畅有画面感，结尾有余味。",
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


def generate_messages(product, emotion_id, custom_prompt="", word_count=""):
    """返回 system + user 消息对"""
    emotion = EMOTION_PROMPTS.get(emotion_id)
    if not emotion:
        emotion = EMOTION_PROMPTS["heartfelt"]

    system = emotion["role"]
    user_template = emotion["instruction"]

    extra_parts = []
    if custom_prompt:
        extra_parts.append(f"\n额外要求：\n{custom_prompt}")
    if word_count:
        extra_parts.append(f"\n字数要求：请控制在 {word_count} 字左右")

    extra = "\n".join(extra_parts)
    user_msg = user_template.replace("{product}", product) + extra
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
        emotion_id = request.form.get("emotion_id", "heartfelt")
        reuse_product = product
        reuse_style = emotion_id
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

        system_msg, user_msg = generate_messages(product, emotion_id, custom_prompt, word_count)
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
                style=emotion_id,
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

    # 解析每条记录的标题和前两段内容
    parsed_items = []
    for item in pagination.items:
        title, emoji, content, tags = parse_result(item.result)
        if not title:
            title = item.product
        # 取前两段作为预览
        preview = ""
        if content:
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            preview = "\n\n".join(paragraphs[:2])

        parsed_items.append({
            "id": item.id,
            "title": title,
            "preview": preview,
            "created_at": item.created_at,
            "is_favorited": item.is_favorited,
            "share_token": item.share_token,
            "raw_result": item.result,
        })

    return render_template("history.html", pagination=pagination, search=search,
                           style_filter=style_filter, date_from=date_from,
                           date_to=date_to, tokens_min=tokens_min, tokens_max=tokens_max,
                           style_list=[c['label'] for c in EMOTION_CARDS],
                           parsed_items=parsed_items)


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



@app.route("/rewrite", methods=["POST"])
@login_required
def rewrite():
    try:
        data = request.get_json()
        if not data:
            return {"ok": False, "error": "请求数据为空"}, 200

        source_text = data.get("text", "")
        action = data.get("action", "")
        emotion_id = data.get("style", "heartfelt")

        if not source_text or action not in REWRITE_INSTRUCTIONS:
            return {"ok": False, "error": "参数无效"}, 200

        instruction = REWRITE_INSTRUCTIONS[action]
        system = "你擅长用画面和细节改写文字，遵循少情绪多画面、少说教多留白的原则。"

        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        prompt = f"""{instruction}

原始文案：
{source_text}

请严格按照以下 JSON 格式返回改写后的结果，不要加任何额外的文字：
{{"title": "改写后的标题", "emoji": "📝", "content": "改写后的正文（多段落，用\n\n分隔）", "tags": ["标签1", "标签2"]}}"""
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
    style_icon = "📝"
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
                    emotion_cards=EMOTION_CARDS)
    return dict(user_token_remaining=0,
                daily_remaining=10,
                emotion_cards=EMOTION_CARDS)


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


@app.route("/daily")
@login_required
def daily():
    return render_template("daily.html")


@app.route("/worlds")
@login_required
def worlds():
    return render_template("worlds.html")


# ============================================================
# 文学体系 API
# ============================================================

@app.route("/api/literary/worlds")
@login_required
def api_literary_worlds():
    """返回所有文学世界"""
    return jsonify({
        "worlds": [
            {
                "id": w,
                "label": WORLD_LABELS.get(w, w),
                "description": WORLD_DESCRIPTIONS.get(w, ""),
            }
            for w in WORLDS
        ]
    })


@app.route("/api/literary/generate", methods=["POST"])
@login_required
def api_literary_generate():
    """文学体系生成短文"""
    data = request.get_json() or {}
    world_id = data.get("world_id")
    emotion_id = data.get("emotion_id")
    length = data.get("length", "short")
    seed_words = data.get("seed_words", "")

    result = generate_short_text(
        world_id=world_id,
        emotion_id=emotion_id,
        seed_words=seed_words,
        length=length,
    )

    return jsonify({
        "ok": True,
        "title": result["title"],
        "content": result["content"],
        "world_id": result.get("world_id", world_id),
        "world_label": result.get("world_label", ""),
    })


@app.route("/api/daily/picks")
@login_required
def api_daily_picks():
    """获取每日摘录"""
    max_count = request.args.get("count", 5, type=int)
    # 简单兴趣匹配：从用户的历史记录中推测
    # 暂用随机兴趣
    picks = get_daily_pick(user_id=current_user.id, max_count=max_count)

    read_ids = get_user_reads(current_user.id)
    for p in picks:
        p["is_read"] = p.get("id") in read_ids

    return jsonify({
        "ok": True,
        "picks": picks,
        "date": date.today().isoformat(),
    })


@app.route("/api/daily/read", methods=["POST"])
@login_required
def api_daily_read():
    """标记摘录为已读"""
    data = request.get_json() or {}
    pick_id = data.get("pick_id")
    if pick_id:
        mark_user_read(current_user.id, pick_id)
    return jsonify({"ok": True})


@app.route("/api/daily/detail")
@login_required
def api_daily_detail():
    """摘录详情（含相关世界推荐）"""
    pick_id = request.args.get("pick_id", "")
    detail = get_daily_detail(pick_id)
    return jsonify({"ok": True, **detail})


@app.route("/api/literary/generate-from-pick", methods=["POST"])
@login_required
def api_generate_from_pick():
    """从摘录生成创作起点"""
    data = request.get_json() or {}
    world_id = data.get("world_id")
    title = data.get("title", "")
    content = data.get("content", "")

    # 基于摘录内容生成相似主题的短文
    result = generate_short_text(
        world_id=world_id or "warmth",
        length="medium",
        seed_words=title,
    )

    return jsonify({
        "ok": True,
        "title": result["title"],
        "content": result["content"],
        "world_id": result.get("world_id", world_id),
        "world_label": result.get("world_label", ""),
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
