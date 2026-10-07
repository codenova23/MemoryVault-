"""Image normalization before photo bytes reach the database."""

from __future__ import annotations

import io
from typing import Any

from PIL import Image, ImageOps


def compress_upload(uploaded_file: Any) -> bytes:
    image = Image.open(uploaded_file)
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=82, optimize=True)
    return output.getvalue()