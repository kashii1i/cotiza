from datetime import datetime
from decimal import Decimal, InvalidOperation


SALE_TEXT_FIELDS = {
    "holder_rut": ("RUT titular", 50),
    "holder_name": ("Nombre y apellido", 200),
    "holder_email": ("Correo", 200),
    "product": ("Producto", 200),
    "billing_rut": ("RUT facturación", 50),
    "billing_legal_name": ("Razón social", 200),
    "business_activity": ("Giro", 200),
    "billing_email": ("Correo facturación", 200),
    "region": ("Región", 100),
    "commune": ("Comuna", 100),
    "address": ("Dirección", 250),
    "phone": ("Teléfono", 50),
    "sale_type": ("Tipo de venta", 100),
    "payment_method": ("Medio de pago", 100),
}


def validate_sale_form(form):
    errors = []
    data = {}

    for field, (label, max_length) in SALE_TEXT_FIELDS.items():
        value = (form.get(field) or "").strip()
        if not value:
            errors.append(f"{label} es obligatorio.")
        elif len(value) > max_length:
            errors.append(f"{label} no puede superar los {max_length} caracteres.")
        data[field] = value

    email_fields = ("holder_email", "billing_email")
    for field in email_fields:
        email = data[field]
        if email and ("@" not in email or "." not in email.rsplit("@", 1)[-1]):
            label = SALE_TEXT_FIELDS[field][0]
            errors.append(f"{label} no tiene un formato válido.")

    try:
        data["sale_date"] = datetime.strptime((form.get("sale_date") or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        errors.append("La fecha de venta es obligatoria y debe ser válida.")

    try:
        data["amount"] = Decimal((form.get("amount") or "").strip())
        if not data["amount"].is_finite() or data["amount"] < 0:
            errors.append("El monto debe ser un número igual o mayor que cero.")
    except (InvalidOperation, ValueError):
        errors.append("El monto es obligatorio y debe ser numérico.")

    return data, errors