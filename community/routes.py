"""InkFlow 社区系统 V1"""
import json as _json
from datetime import datetime, timezone, timedelta

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify
)
from flask_login import login_required, current_user
from sqlalchemy import func

from models import db, User, Post, Like, Favorite
from auth.routes import check_sensitive

community_bp = Blueprint("community", __name__, url_prefix="/community")

ALL_TAGS = [
    "遗憾", "青春", "成长", "暗恋", "离别", "亲情", "爱情",
    "梦想", "生活", "故事", "随笔", "想念", "孤独", "治愈",
    "友情", "童年", "时光", "远方",
]

CONTENT_BLOCK_KEYWORDS = [
    "杀人", "自杀", "贩毒", "赌博", "走私",
    "加微信", "加qq", "加vx", "微信号", "qq号", "手机号", "联系电话",
    "扫码进群", "点击链接", "关注公众号", "私聊我",
    "免费领取", "转发抽奖", "点赞抽奖", "送红包",
    "傻逼", "操你妈", "去死", "废物", "垃圾",
]


def check_content_blocked(text):
    if not text:
        return True, None
    t = text.lower()
    for word in CONTENT_BLOCK_KEYWORDS:
        if word in t or word in text:
            return False, word
    return True, None


def format_post(p):
    tags = []
    if p.tags:
        try:
            tags = _json.loads(p.tags)
        except Exception:
            tags = [p.tags]
    return {
        "id": p.id,
        "title": p.title,
        "content_preview": (p.content[:120] + "...") if len(p.content) > 120 else p.content,
        "author_id": p.user_id,
        "author_name": p.author_nick,
        "author_avatar": p.author.avatar_url or "",
        "created_at": p.created_at.strftime("%m-%d %H:%M"),
        "tags": tags,
        "like_count": p.like_count,
        "fav_count": p.fav_count,
        "view_count": p.view_count,
    }


@community_bp.route("")
def index():
    tab = request.args.get("tab", "latest")
    page = request.args.get("page", 1, type=int)
    per_page = 12

    if tab == "hot":
        query = Post.query.filter_by(is_visible=True).order_by(
            (Post.like_count * 3 + Post.fav_count * 2 + Post.view_count).desc(),
            Post.created_at.desc()
        )
    elif tab == "random":
        query = Post.query.filter_by(is_visible=True).order_by(func.random())
    else:
        query = Post.query.filter_by(is_visible=True).order_by(Post.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    posts = [format_post(p) for p in pagination.items]

    return render_template(
        "community/index.html", posts=posts, pagination=pagination, tab=tab,
        is_logged_in=current_user.is_authenticated
    )


@community_bp.route("/publish", methods=["GET", "POST"])
@login_required
def publish():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        tags_raw = request.form.get("tags", "[]").strip()

        if not title or not content:
            flash("标题和正文不能为空", "error")
            return render_template("community/publish.html", all_tags=ALL_TAGS)
        if len(title) > 200:
            flash("标题不能超过200字", "error")
            return render_template("community/publish.html", all_tags=ALL_TAGS)
        if len(content) > 20000:
            flash("正文不能超过20000字", "error")
            return render_template("community/publish.html", all_tags=ALL_TAGS)

        for target, label in [(title, "标题"), (content, "正文")]:
            ok, w = check_sensitive(target)
            if not ok:
                flash(f"{label}包含敏感词「{w}」", "error")
                return render_template("community/publish.html", all_tags=ALL_TAGS)
            ok2, w2 = check_content_blocked(target)
            if not ok2:
                flash(f"{label}包含违规内容「{w2}」", "error")
                return render_template("community/publish.html", all_tags=ALL_TAGS)

        try:
            tags_list = _json.loads(tags_raw)
            if not isinstance(tags_list, list):
                tags_list = []
        except Exception:
            tags_list = []

        seen = set()
        tags_clean = []
        for t in tags_list:
            t = str(t).strip()
            if t and t not in seen and t in ALL_TAGS:
                tags_clean.append(t)
                seen.add(t)

        post = Post(
            user_id=current_user.id,
            title=title,
            content=content,
            tags=_json.dumps(tags_clean, ensure_ascii=False),
            is_visible=True,
        )
        db.session.add(post)
        db.session.commit()
        flash("作品发布成功！", "success")
        return redirect(url_for("community.post_detail", post_id=post.id))

    return render_template("community/publish.html", all_tags=ALL_TAGS)


@community_bp.route("/post/<int:post_id>")
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    if not post.is_visible:
        flash("作品已隐藏", "error")
        return redirect(url_for("community.index"))

    # 阅读量 +1（用 Cookie 去重，简化处理）
    post.view_count += 1
    db.session.commit()

    tags = []
    if post.tags:
        try:
            tags = _json.loads(post.tags)
        except Exception:
            tags = [post.tags]

    user_liked = False
    user_faved = False
    if current_user.is_authenticated:
        user_liked = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first() is not None
        user_faved = Favorite.query.filter_by(user_id=current_user.id, post_id=post.id).first() is not None

    return render_template(
        "community/detail.html", post=post, tags=tags, author=post.author,
        user_liked=user_liked, user_faved=user_faved,
        is_author=(current_user.is_authenticated and current_user.id == post.user_id),
        is_logged_in=current_user.is_authenticated,
    )


@community_bp.route("/user/<int:user_id>")
def user_page(user_id):
    author = User.query.get_or_404(user_id)
    page = request.args.get("page", 1, type=int)
    pagination = Post.query.filter_by(user_id=user_id, is_visible=True)\
        .order_by(Post.created_at.desc())\
        .paginate(page=page, per_page=12, error_out=False)

    total_posts = Post.query.filter_by(user_id=user_id, is_visible=True).count()
    total_likes = db.session.query(func.sum(Post.like_count))\
        .filter(Post.user_id == user_id, Post.is_visible == True).scalar() or 0

    posts = [format_post(p) for p in pagination.items]

    return render_template(
        "community/user.html", author=author, posts=posts, pagination=pagination,
        total_posts=total_posts, total_likes=total_likes,
        is_self=(current_user.is_authenticated and current_user.id == user_id),
    )


@community_bp.route("/favorites")
@login_required
def my_favorites():
    page = request.args.get("page", 1, type=int)
    favs = Favorite.query.filter_by(user_id=current_user.id)\
        .order_by(Favorite.created_at.desc())\
        .paginate(page=page, per_page=12, error_out=False)

    posts = []
    for fav in favs.items:
        p = db.session.get(Post, fav.post_id)
        if not p or not p.is_visible:
            continue
        posts.append(format_post(p))

    return render_template("community/favorites.html", posts=posts, pagination=favs)


@community_bp.route("/api/like/<int:post_id>", methods=["POST"])
@login_required
def api_like(post_id):
    post = Post.query.get_or_404(post_id)
    if not post.is_visible:
        return {"ok": False, "error": "作品不存在"}, 404

    existing = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if existing:
        db.session.delete(existing)
        post.like_count = max(0, post.like_count - 1)
        db.session.commit()
        return {"ok": True, "liked": False, "count": post.like_count}

    like = Like(user_id=current_user.id, post_id=post_id)
    db.session.add(like)
    post.like_count += 1
    db.session.commit()
    return {"ok": True, "liked": True, "count": post.like_count}


@community_bp.route("/api/fav/<int:post_id>", methods=["POST"])
@login_required
def api_fav(post_id):
    post = Post.query.get_or_404(post_id)
    if not post.is_visible:
        return {"ok": False, "error": "作品不存在"}, 404

    existing = Favorite.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if existing:
        db.session.delete(existing)
        post.fav_count = max(0, post.fav_count - 1)
        db.session.commit()
        return {"ok": True, "faved": False, "count": post.fav_count}

    fav = Favorite(user_id=current_user.id, post_id=post_id)
    db.session.add(fav)
    post.fav_count += 1
    db.session.commit()
    return {"ok": True, "faved": True, "count": post.fav_count}


@community_bp.route("/api/share/<int:post_id>", methods=["POST"])
@login_required
def api_share(post_id):
    post = Post.query.get_or_404(post_id)
    if not post.is_visible:
        return {"ok": False, "error": "作品不存在"}, 404
    post.share_count += 1
    db.session.commit()
    return {"ok": True, "count": post.share_count}


@community_bp.route("/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    """删除自己的社区作品（级联删除关联的点赞和收藏记录）"""
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        flash("无权限删除", "error")
        return redirect(url_for("community.index"))

    # 删除关联的点赞记录
    Like.query.filter_by(post_id=post_id).delete()
    # 删除关联的收藏记录
    Favorite.query.filter_by(post_id=post_id).delete()
    # 删除文章本身
    db.session.delete(post)
    db.session.commit()

    flash("文章已删除", "success")
    return redirect(url_for("community.index"))


@community_bp.route("/share/<int:post_id>")
def share_card(post_id):
    post = Post.query.get_or_404(post_id)
    if not post.is_visible:
        return "作品不存在", 404

    tags = []
    if post.tags:
        try:
            tags = _json.loads(post.tags)
        except Exception:
            tags = [post.tags]

    excerpt = post.content[:200] + ("..." if len(post.content) > 200 else "")
    return render_template(
        "community/share_card.html", post=post, author=post.author,
        tags=tags, excerpt=excerpt, site_url=request.host_url,
    )


@community_bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    tag = request.args.get("tag", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Post.query.filter_by(is_visible=True)

    if q:
        query = query.filter(
            db.or_(Post.title.contains(q), Post.content.contains(q))
        )
    if tag and tag in ALL_TAGS:
        query = query.filter(Post.tags.contains(tag))

    pagination = query.order_by(Post.created_at.desc())\
        .paginate(page=page, per_page=12, error_out=False)

    posts = [format_post(p) for p in pagination.items]

    return render_template(
        "community/search.html", posts=posts, pagination=pagination,
        q=q, tag=tag, all_tags=ALL_TAGS,
    )
