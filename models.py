from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone
import hashlib

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # Token 统计
    total_tokens = db.Column(db.Integer, default=0)
    # 免费用户限制 10000 tokens/月
    token_limit = db.Column(db.Integer, default=10000)
    # 每日生成次数
    daily_count = db.Column(db.Integer, default=0)
    daily_date = db.Column(db.String(10), default="")
    # 是否为付费用户
    is_premium = db.Column(db.Boolean, default=False)
    # API Key 管理
    api_key = db.Column(db.String(200), default="")
    backup_api_key = db.Column(db.String(200), default="")
    # 微信登录
    wechat_openid = db.Column(db.String(64), unique=True, nullable=True)
    wechat_unionid = db.Column(db.String(64), nullable=True)
    avatar_url = db.Column(db.String(500), default="")
    nickname = db.Column(db.String(80), default="")

    histories = db.relationship("History", backref="user", lazy=True, order_by="History.created_at.desc()")

    def set_password(self, password):
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

    @property
    def tokens_remaining(self):
        if self.is_premium:
            return "无限制"
        return max(0, self.token_limit - self.total_tokens)


class History(db.Model):
    __tablename__ = "histories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product = db.Column(db.String(200), nullable=False)
    style = db.Column(db.String(50), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    result = db.Column(db.Text, nullable=False)
    tokens_used = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_favorited = db.Column(db.Boolean, default=False)
    share_token = db.Column(db.String(64), default="")


class Post(db.Model):
    """社区作品"""
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(500), default="")  # JSON 字符串 ["青春","成长"]
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_visible = db.Column(db.Boolean, default=True)  # 审核通过

    # 统计
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    fav_count = db.Column(db.Integer, default=0)
    share_count = db.Column(db.Integer, default=0)

    # 最近 7/30 天阅读量（每日定时任务更新，暂时先只记录总阅读）
    view_7d = db.Column(db.Integer, default=0)
    view_30d = db.Column(db.Integer, default=0)

    author = db.relationship("User", backref="posts", lazy=True, foreign_keys=[user_id])

    @property
    def author_nick(self):
        return self.author.nickname or self.author.username

    @property
    def author_avatar(self):
        return self.author.avatar_url or ""


class Like(db.Model):
    """点赞记录"""
    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint("user_id", "post_id", name="uq_like"),)


class Favorite(db.Model):
    """收藏记录（社区作品 + 摘录）"""
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=True)
    pick_id = db.Column(db.String(64), nullable=True)  # 摘录收藏
    pick_data = db.Column(db.Text, default="")         # 摘录快照（JSON）
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint("user_id", "post_id", name="uq_fav"),
                      db.UniqueConstraint("user_id", "pick_id", name="uq_fav_pick"),)

