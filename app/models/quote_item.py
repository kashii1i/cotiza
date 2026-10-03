from app.extensions import db


class QuoteItem(db.Model):
    __tablename__ = "quote_items"

    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey("quotes.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    signer_type = db.Column(db.String(30), nullable=False, default="token")
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    manual_price = db.Column(db.Numeric(12, 2), nullable=True, default=None)
    discount_percent = db.Column(db.Integer, nullable=False, default=0)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    quote = db.relationship("Quote", back_populates="items")
    product = db.relationship("Product")

    def __repr__(self):
        return f"<QuoteItem {self.id}>"
