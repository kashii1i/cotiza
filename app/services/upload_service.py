from pathlib import Path
from uuid import uuid4

from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PAYMENT_PROOF_DIR = BASE_DIR / "uploads" / "payment_proofs"
ALLOWED_PROOF_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "webp"}


def save_payment_proof(upload):
    original_name = secure_filename(upload.filename or "")
    if not original_name or "." not in original_name:
        return None, "Selecciona una imagen o un archivo PDF como comprobante."

    extension = original_name.rsplit(".", 1)[1].lower()
    if extension not in ALLOWED_PROOF_EXTENSIONS:
        return None, "El comprobante debe ser PDF, PNG, JPG o WEBP."

    signature = upload.stream.read(12)
    upload.stream.seek(0)
    valid_signatures = {
        "pdf": signature.startswith(b"%PDF-"),
        "png": signature.startswith(b"\x89PNG\r\n\x1a\n"),
        "jpg": signature.startswith(b"\xff\xd8\xff"),
        "jpeg": signature.startswith(b"\xff\xd8\xff"),
        "webp": signature.startswith(b"RIFF") and signature[8:12] == b"WEBP",
    }
    if not valid_signatures[extension]:
        return None, "El contenido del comprobante no coincide con su formato de archivo."

    PAYMENT_PROOF_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}.{extension}"
    upload.save(PAYMENT_PROOF_DIR / stored_name)
    return stored_name, None