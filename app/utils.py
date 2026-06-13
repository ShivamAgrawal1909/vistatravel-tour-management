import secrets
import uuid
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename

ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def save_upload(file_storage, subfolder: str = "") -> str | None:
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None
    ext = secure_filename(file_storage.filename).rsplit(".", 1)[-1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    base: Path = current_app.config["UPLOAD_FOLDER"]
    dest = base / subfolder if subfolder else base
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / name
    file_storage.save(path)
    rel = f"uploads/{subfolder}/{name}" if subfolder else f"uploads/{name}"
    return rel.replace("\\", "/")


def generate_public_booking_id() -> str:
    return secrets.token_hex(4).upper()


def generate_recovery_token() -> str:
    return secrets.token_urlsafe(32)
