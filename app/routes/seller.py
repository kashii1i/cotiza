import os
from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, send_from_directory, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models.product import Product
from app.models.quote import Quote
from app.models.quote_item import QuoteItem
from app.services.pdf_service import generate_quote_pdf
from app.models.sale import Sale
from app.services.sale_service import validate_sale_form
from app.services.quote_service import calculate_totals_for_items, validate_quote_request
from app.services.upload_service import PAYMENT_PROOF_DIR, save_payment_proof

seller_bp = Blueprint("seller", __name__)


@seller_bp.route("/dashboard")
@login_required
def dashboard():
    quotes = Quote.query.filter_by(seller_id=current_user.id).order_by(Quote.created_at.desc()).all()
    return render_template("seller/dashboard.html", quotes=quotes)


@seller_bp.route("/sales")
@login_required
def sales():
    sales_list = Sale.query.filter_by(seller_id=current_user.id).order_by(Sale.sale_date.desc(), Sale.id.desc()).all()
    return render_template("seller/sales.html", sales=sales_list)


@seller_bp.route("/sales/new", methods=["GET", "POST"])
@login_required
def new_sale():
    if request.method == "POST":
        data, errors = validate_sale_form(request.form)

        upload = request.files.get("payment_proof")
        if upload is None or not upload.filename:
            errors.append("Debes adjuntar el comprobante de pago.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("seller/sale_form.html", form_data=request.form)

        filename, error = save_payment_proof(upload)
        if error:
            flash(error, "error")
            return render_template("seller/sale_form.html", form_data=request.form)

        sale = Sale(
            seller_id=current_user.id,
            payment_proof_filename=filename,
            **data,
        )
        db.session.add(sale)
        db.session.commit()
        flash("Venta ingresada correctamente.", "success")
        destination = "admin.sales" if current_user.is_admin else "seller.sales"
        return redirect(url_for(destination))

    return render_template("seller/sale_form.html", form_data={})


@seller_bp.route("/sales/<int:sale_id>/proof")
@login_required
def download_sale_proof(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    if not current_user.is_admin and sale.seller_id != current_user.id:
        abort(403)
    return send_from_directory(PAYMENT_PROOF_DIR, sale.payment_proof_filename, as_attachment=True)


@seller_bp.route("/quotes/<int:quote_id>/status", methods=["POST"])
@login_required
def update_quote_status(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    if quote.seller_id != current_user.id:
        flash("No tienes permisos para cambiar esta cotización.", "error")
        return redirect(url_for("seller.dashboard"))

    new_status = (request.form.get("status") or "").strip()
    if new_status not in {"Pendiente", "Completada"}:
        flash("El estado seleccionado no es válido.", "error")
        return redirect(url_for("seller.dashboard"))

    quote.status = new_status
    db.session.commit()
    flash("Estado de la cotización actualizado correctamente.", "success")
    return redirect(url_for("seller.dashboard"))


@seller_bp.route("/quotes/new", methods=["GET", "POST"])
@login_required
def new_quote():
    products = Product.query.filter_by(is_active=True).all()

    if request.method == "POST":
        payload = validate_quote_request(request.form)

        if payload["errors"]:
            for error in payload["errors"]:
                flash(error, "error")
            return render_template("seller/quote_form.html", products=products, form_data=request.form)

        quote_items = []
        for item in payload["items"]:
            product = Product.query.get(item["product_id"])
            if not product:
                flash(f"El producto seleccionado en la fila no existe: {item['product_id']}", "error")
                return render_template("seller/quote_form.html", products=products, form_data=request.form)
            item["product"] = product
            quote_items.append(item)

        totals = calculate_totals_for_items(quote_items, payload["discount_percent"])

        try:
            due_date = datetime.strptime(payload["due_date"], "%Y-%m-%d").date() if payload["due_date"] else None
        except ValueError:
            flash("La fecha de vencimiento no es válida.", "error")
            return render_template("seller/quote_form.html", products=products, form_data=request.form)

        quote = Quote(
            quote_number=Quote.generate_number(),
            seller_id=current_user.id,
            client_rut=payload["client_rut"],
            client_razon_social=payload["client_razon_social"],
            payment_method=payload["payment_method"],
            conditions=payload["conditions"],
            bank_details=payload["bank_details"],
            status="Pendiente",
            due_date=due_date,
            subtotal=totals["subtotal"],
            discount_percent=totals["discount_percent"],
            discount_amount=totals["discount_amount"],
            iva=totals["iva"],
            total=totals["total"],
        )

        db.session.add(quote)
        db.session.flush()

        for item in totals["items"]:
            quote_item = QuoteItem(
                quote_id=quote.id,
                product_id=item["product"].id,
                signer_type="sin_firmador",
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                manual_price=item.get("manual_price", item["unit_price"]),
                discount_percent=0,
                subtotal=item["line_subtotal"],
            )
            db.session.add(quote_item)

        db.session.commit()
        generate_quote_pdf(quote)
        db.session.commit()

        flash("Cotización creada correctamente.", "success")
        return redirect(url_for("seller.dashboard"))

    return render_template("seller/quote_form.html", products=products, form_data={})


@seller_bp.route("/quotes/<int:quote_id>/pdf")
@login_required
def download_quote_pdf(quote_id):
    quote = Quote.query.get_or_404(quote_id)

    if current_user.role != "admin" and quote.seller_id != current_user.id:
        flash("No tienes permisos para acceder a esta cotización.", "error")
        return redirect(url_for("seller.dashboard"))

    if not quote.pdf_path or not os.path.exists(quote.pdf_path):
        generate_quote_pdf(quote)
        db.session.commit()

    return send_file(
        quote.pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{quote.quote_number}.pdf",
    )
