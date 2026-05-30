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

