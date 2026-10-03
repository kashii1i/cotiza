from datetime import datetime

from app.extensions import db


class Quote(db.Model):
    __tablename__ = "quotes"

    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.Date, nullable=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    seller = db.relationship("User", backref="quotes")

    client_rut = db.Column(db.String(50), nullable=False)
    client_razon_social = db.Column(db.String(200), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False, default="Transferencia")
    conditions = db.Column(db.Text, nullable=True, default="")
    bank_details = db.Column(db.Text, nullable=True, default="")
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    discount_percent = db.Column(db.Integer, nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    iva = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    status = db.Column(db.String(30), nullable=False, default="Pendiente")
    pdf_path = db.Column(db.String(255), nullable=True)

    items = db.relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")

    @staticmethod
    def generate_number():
        last_quote = Quote.query.order_by(Quote.id.desc()).first()
        next_id = (last_quote.id + 1) if last_quote else 1
        return f"COT-{next_id:05d}"

    def __repr__(self):
        return f"<Quote {self.quote_number}>"
