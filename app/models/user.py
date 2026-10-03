from flask_login import UserMixin

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="seller")

    def __repr__(self):
        return f"<User {self.username!r} ({self.role})>"

    @property
    def is_admin(self):
        return self.role == "admin"
