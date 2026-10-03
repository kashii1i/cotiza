from datetime import datetime

from app.extensions import db


class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey("quotes.id"), nullable=True, unique=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    sale_date = db.Column(db.Date, nullable=False)
    holder_rut = db.Column(db.String(50), nullable=False)
    holder_name = db.Column(db.String(200), nullable=False)
    holder_email = db.Column(db.String(200), nullable=False)
    product = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    billing_rut = db.Column(db.String(50), nullable=False)
    billing_legal_name = db.Column(db.String(200), nullable=False)
    business_activity = db.Column(db.String(200), nullable=False)
    billing_email = db.Column(db.String(200), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    commune = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    sale_type = db.Column(db.String(100), nullable=False)
    payment_method = db.Column(db.String(100), nullable=False)
    payment_proof_filename = db.Column(db.String(255), nullable=False)
    invoice_correlative = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    seller = db.relationship("User", backref="sales")
    quote = db.relationship("Quote", backref=db.backref("sale", uselist=False))

    def __repr__(self):
        return f"<Sale {self.id} holder={self.holder_rut}>"