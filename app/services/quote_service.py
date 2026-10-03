from decimal import Decimal, InvalidOperation

from app.models.product import Product


def validate_quote_request(form):
    errors = []
    client_rut = (form.get("client_rut") or "").strip()
    client_razon_social = (form.get("client_razon_social") or "").strip()
    product_ids = form.getlist("product_id")
    quantities = form.getlist("quantity")
    manual_prices = form.getlist("manual_price")
    raw_discount_percent = (form.get("discount_percent") or "0").strip()

    if not client_rut:
        errors.append("El RUT del cliente es obligatorio.")

    if not client_razon_social:
        errors.append("La razón social del cliente es obligatoria.")

    try:
        discount_percent = int(raw_discount_percent)
    except (TypeError, ValueError):
        discount_percent = 0
        errors.append("El descuento de la cotización debe ser un número entero.")

    if discount_percent < 0 or discount_percent > 100:
        errors.append("El descuento de la cotización debe estar entre 0 y 100.")

    items = []
    for index, product_id in enumerate(product_ids):
        if not product_id:
            continue

        raw_quantity = quantities[index] if index < len(quantities) else "1"
        raw_manual_price = manual_prices[index] if index < len(manual_prices) else ""

        try:
            quantity = int(raw_quantity)
        except (TypeError, ValueError):
            errors.append(f"La cantidad del producto {index + 1} debe ser un número entero.")
            continue

        if quantity <= 0:
            errors.append(f"La cantidad del producto {index + 1} debe ser mayor que cero.")
            continue

        product = Product.query.get(int(product_id)) if product_id else None
        if not product:
            errors.append(f"El producto seleccionado en la fila {index + 1} no existe.")
            continue

        try:
            manual_price = Decimal(str(raw_manual_price)) if raw_manual_price not in (None, "") else Decimal("0")
        except InvalidOperation:
            errors.append(f"El valor unitario del producto {index + 1} debe ser numérico.")
            continue

        if manual_price <= 0:
            errors.append(f"El valor unitario del producto {index + 1} debe ser mayor que cero.")
            continue

        items.append({
            "product_id": product.id,
            "quantity": quantity,
            "manual_price": manual_price,
            "product": product,
        })

    if not items:
        errors.append("Debe agregar al menos un producto a la cotización.")

    return {
        "client_rut": client_rut,
        "client_razon_social": client_razon_social,
        "errors": errors,
        "items": items,
        "discount_percent": discount_percent,
        "payment_method": (form.get("payment_method") or "Transferencia").strip(),
        "conditions": (form.get("conditions") or "").strip(),
        "bank_details": (form.get("bank_details") or "").strip(),
        "due_date": (form.get("due_date") or "").strip(),
    }


def calculate_totals_for_items(items, discount_percent=0):
    subtotal = Decimal("0")
    calculated_items = []

    for item in items:
        product = item["product"]
        quantity = Decimal(str(item["quantity"]))
        unit_price = Decimal(str(item["manual_price"]))
        line_subtotal = unit_price * quantity

        subtotal += line_subtotal
        calculated_items.append({
            "product": product,
            "quantity": item["quantity"],
            "unit_price": unit_price,
            "line_subtotal": line_subtotal,
            "manual_price": item.get("manual_price", unit_price),
        })

    discount_percent = Decimal(str(discount_percent))
    discount_amount = subtotal * discount_percent / Decimal("100")
    taxable_subtotal = subtotal - discount_amount
    iva = taxable_subtotal * Decimal("0.19")
    total = taxable_subtotal + iva

    return {
        "items": calculated_items,
        "subtotal": subtotal,
        "discount_percent": int(discount_percent),
        "discount_amount": discount_amount,
        "taxable_subtotal": taxable_subtotal,
        "iva": iva,
        "total": total,
    }
