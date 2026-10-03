from flask import Flask
from sqlalchemy import inspect
from werkzeug.security import generate_password_hash

from app.config import Config
from app.extensions import db, login_manager
from app.models import Sale
from app.models.product import Product
from app.models.user import User
from app.routes.admin import admin_bp
from app.routes.auth import auth_bp
from app.routes.main import main_bp
from app.routes.seller import seller_bp


def ensure_quote_item_columns():
    inspector = inspect(db.engine)
    if "quote_items" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("quote_items")}
    if "signer_type" not in columns:
        db.session.execute(db.text("ALTER TABLE quote_items ADD COLUMN signer_type VARCHAR(30) DEFAULT 'token' NOT NULL"))
    if "manual_price" not in columns:
        db.session.execute(db.text("ALTER TABLE quote_items ADD COLUMN manual_price NUMERIC(12, 2)"))
    db.session.commit()


def ensure_quote_discount_columns():
    inspector = inspect(db.engine)
    if "quotes" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("quotes")}
    if "discount_percent" not in columns:
        db.session.execute(db.text("ALTER TABLE quotes ADD COLUMN discount_percent INTEGER DEFAULT 0 NOT NULL"))
    if "discount_amount" not in columns:
        db.session.execute(db.text("ALTER TABLE quotes ADD COLUMN discount_amount NUMERIC(12, 2) DEFAULT 0 NOT NULL"))
    db.session.commit()


def ensure_sale_columns():
    inspector = inspect(db.engine)
    if "sales" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("sales")}
    required_columns = {
        "seller_id", "sale_date", "holder_rut", "holder_name", "holder_email",
        "product", "amount", "billing_rut", "billing_legal_name", "business_activity",
        "billing_email", "region", "commune", "address", "phone", "sale_type", "payment_method",
    }
    if required_columns.issubset(columns):
        return
    if db.engine.dialect.name != "sqlite":
        raise RuntimeError("La migración de ventas actualizadas requiere migrar la tabla sales antes de iniciar.")

    db.session.execute(db.text("""
        CREATE TABLE sales_new (
            id INTEGER PRIMARY KEY,
            quote_id INTEGER UNIQUE,
            seller_id INTEGER NOT NULL,
            sale_date DATE NOT NULL,
            holder_rut VARCHAR(50) NOT NULL,
            holder_name VARCHAR(200) NOT NULL,
            holder_email VARCHAR(200) NOT NULL,
            product VARCHAR(200) NOT NULL,
            amount NUMERIC(12, 2) NOT NULL,
            billing_rut VARCHAR(50) NOT NULL,
            billing_legal_name VARCHAR(200) NOT NULL,
            business_activity VARCHAR(200) NOT NULL,
            billing_email VARCHAR(200) NOT NULL,
            region VARCHAR(100) NOT NULL,
            commune VARCHAR(100) NOT NULL,
            address VARCHAR(250) NOT NULL,
            phone VARCHAR(50) NOT NULL,
            sale_type VARCHAR(100) NOT NULL,
            payment_method VARCHAR(100) NOT NULL,
            payment_proof_filename VARCHAR(255) NOT NULL,
            invoice_correlative VARCHAR(100),
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            FOREIGN KEY(quote_id) REFERENCES quotes(id),
            FOREIGN KEY(seller_id) REFERENCES users(id)
        )
    """))
    db.session.execute(db.text("""
        INSERT INTO sales_new (
            id, quote_id, seller_id, sale_date, holder_rut, holder_name, holder_email,
            product, amount, billing_rut, billing_legal_name, business_activity,
            billing_email, region, commune, address, phone, sale_type, payment_method,
            payment_proof_filename, invoice_correlative, created_at, updated_at
        )
        SELECT sales.id, sales.quote_id, quotes.seller_id,
            substr(CAST(quotes.created_at AS TEXT), 1, 10),
            COALESCE(quotes.client_rut, ''), COALESCE(quotes.client_razon_social, ''), '',
            COALESCE((
                SELECT group_concat(products.name, ', ')
                FROM quote_items JOIN products ON products.id = quote_items.product_id
                WHERE quote_items.quote_id = quotes.id
            ), ''),
            COALESCE(quotes.total, 0), '', '', '', '', '', '', '', '', '',
            COALESCE(quotes.payment_method, ''), sales.payment_proof_filename,
            sales.invoice_correlative, sales.created_at, sales.updated_at
        FROM sales JOIN quotes ON quotes.id = sales.quote_id
    """))
    db.session.execute(db.text("DROP TABLE sales"))
    db.session.execute(db.text("ALTER TABLE sales_new RENAME TO sales"))
    db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(seller_bp, url_prefix="/seller")

    with app.app_context():
        db.create_all()
        ensure_quote_item_columns()
        ensure_quote_discount_columns()
        ensure_sale_columns()
        clear_legacy_product_prices()
        seed_default_users()
        seed_default_products()

    return app


def seed_default_users():
    if not User.query.filter_by(username="admin").first():
        admin_user = User(
            username="admin",
            password_hash=generate_password_hash("admin123"),
            role="admin",
        )
        db.session.add(admin_user)

    if not User.query.filter_by(username="vendedor").first():
        seller_user = User(
            username="vendedor",
            password_hash=generate_password_hash("vendedor123"),
            role="seller",
        )
        db.session.add(seller_user)

    db.session.commit()


def seed_default_products():
    products = [
        Product(name="Firmador web", category="web", price=0, is_active=True),
        Product(name="Firmador token", category="token", price=0, is_active=True),
        Product(name="Firma Electrónica Avanzada - 1 año", category="fea", price=0, is_active=True),
        Product(name="Firma Electrónica Avanzada - 2 años", category="fea", price=0, is_active=True),
        Product(name="Firma Electrónica Avanzada - 3 años", category="fea", price=0, is_active=True),
        Product(name="Firma Electrónica Simple - 6 meses", category="fes", price=0, is_active=True),
        Product(name="Firma Electrónica Simple - 1 año", category="fes", price=0, is_active=True),
        Product(name="Firma Electrónica Simple - 2 años", category="fes", price=0, is_active=True),
        Product(name="Firma Electrónica Simple - 3 años", category="fes", price=0, is_active=True),
    ]

    existing_names = {name for (name,) in db.session.query(Product.name).all()}
    missing_products = [product for product in products if product.name not in existing_names]
    if missing_products:
        db.session.add_all(missing_products)
        db.session.commit()


def clear_legacy_product_prices():
    Product.query.filter(Product.price != 0).update(
        {Product.price: 0},
        synchronize_session=False,
    )
    db.session.commit()
