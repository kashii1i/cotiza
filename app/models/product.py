from app.extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False, default="general")
    price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<Product {self.name!r}>"
