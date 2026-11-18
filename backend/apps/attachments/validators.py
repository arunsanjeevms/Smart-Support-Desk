"""
Checks every uploaded file before it is stored.

* The extension must be allowed (``SUPPORT_DESK["ATTACHMENTS"]["ALLOWED_EXTENSIONS"]``)
  *and* known to this module - unknown types can never be switched on by config.
* Size and number of files are limited.
* The first bytes must match the type: a ``.png`` must really be a PNG, a ``.pdf``
  a PDF, Office files and ``.zip`` a ZIP container, and text files must not
  contain binary data. A renamed executable is therefore rejected.
* SVG, HTML and scripts are not supported at all (they could run code in a browser).
"""

import re
from dataclasses import dataclass

from django.conf import settings
from rest_framework.exceptions import ValidationError

# Every type the app knows how to accept, with the Content-Type it is served with.
CONTENT_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
    "pdf": "application/pdf",
    "txt": "text/plain",
    "log": "text/plain",
    "csv": "text/csv",
    "json": "application/json",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "zip": "application/zip",
}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
TEXT_EXTENSIONS = {"txt", "log", "csv", "json"}
ZIP_EXTENSIONS = {"xlsx", "docx", "zip"}

_SIGNATURES = {
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "gif": (b"GIF87a", b"GIF89a"),
    "pdf": (b"%PDF-",),
    "xlsx": (b"PK\x03\x04",),
    "docx": (b"PK\x03\x04",),
    "zip": (b"PK\x03\x04", b"PK\x05\x06"),
}
_UNSAFE_NAME_CHARS = re.compile(r'[\x00-\x1f\x7f<>:"/\\|?*]+')


def attachment_settings() -> dict:
    return settings.SUPPORT_DESK["ATTACHMENTS"]


def allowed_extensions() -> list[str]:
    """Allowed by the configuration and supported by the app, in a stable order."""
    configured = {ext.lower().lstrip(".") for ext in attachment_settings()["ALLOWED_EXTENSIONS"]}
    return [ext for ext in CONTENT_TYPES if ext in configured]


def human_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.0f} KB"
    return f"{size} bytes"


def clean_file_name(name: str) -> str:
    """Drop any folder part and characters that are unsafe in a file name; keep it readable."""
    name = re.split(r"[\\/]", name or "")[-1]
    name = " ".join(_UNSAFE_NAME_CHARS.sub(" ", name).split()).strip(" .")
    if len(name) > 150:
        stem, dot, ext = name.rpartition(".")
        name = f"{stem[: 149 - len(ext)]}.{ext}" if dot else name[:150]
    return name or "file"


def _matches_type(extension: str, head: bytes) -> bool:
    if extension == "webp":
        return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    if extension in TEXT_EXTENSIONS:
        return b"\x00" not in head
    return head.startswith(_SIGNATURES[extension])


@dataclass(frozen=True)
class CheckedFile:
    file: object  # Django UploadedFile
    name: str
    extension: str
    content_type: str
    size: int


def validate_files(files) -> list[CheckedFile]:
    """Validate a whole upload; raises one ValidationError listing every problem."""
    config = attachment_settings()
    max_files = config["MAX_FILES"]
    max_bytes = config["MAX_FILE_MB"] * 1024 * 1024
    allowed = allowed_extensions()

    files = list(files or [])
    if not files:
        raise ValidationError({"files": ["Choose at least one file."]})
    if len(files) > max_files:
        raise ValidationError({"files": [f"You can attach up to {max_files} files at a time."]})

    checked, problems = [], []
    for upload in files:
        name = clean_file_name(upload.name)
        extension = name.rpartition(".")[2].lower() if "." in name else ""
        if extension not in allowed:
            problems.append(f"{name}: this file type is not allowed. Allowed: {', '.join(allowed)}.")
            continue
        if upload.size == 0:
            problems.append(f"{name} is empty.")
            continue
        if upload.size > max_bytes:
            problems.append(
                f"{name} is {human_size(upload.size)}; the limit is {config['MAX_FILE_MB']} MB per file."
            )
            continue
        upload.seek(0)
        head = upload.read(8192)
        upload.seek(0)
        if not _matches_type(extension, head):
            problems.append(f"{name} does not look like a real .{extension} file.")
            continue
        checked.append(CheckedFile(upload, name, extension, CONTENT_TYPES[extension], upload.size))

    if problems:
        raise ValidationError({"files": problems})
    return checked
