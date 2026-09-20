"""Generate N similar image variations (local PIL transforms + optional OpenAI)."""

from __future__ import annotations

import os
import random
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def _local_variants(src: Path, out_dir: Path, n: int = 3) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    w, h = im.size
    paths: list[Path] = []
    ops = [
        lambda i: ImageEnhance.Color(i).enhance(1.12),
        lambda i: ImageEnhance.Contrast(i).enhance(1.08),
        lambda i: ImageEnhance.Brightness(i).enhance(1.05),
        lambda i: i.filter(ImageFilter.UnsharpMask(radius=1.2, percent=80, threshold=2)),
        lambda i: ImageOps.autocontrast(i, cutoff=1),
    ]
    rng = random.Random(hash(src.name) & 0xFFFFFFFF)
    for idx in range(n):
        crop = 0.02 + (idx * 0.01)
        left = int(w * crop * (0.4 + 0.2 * (idx % 3)))
        top = int(h * crop * (0.3 + 0.2 * ((idx + 1) % 3)))
        right = w - int(w * crop * (0.3 + 0.15 * ((idx + 2) % 3)))
        bottom = h - int(h * crop * (0.35 + 0.1 * (idx % 2)))
        if right <= left + 32 or bottom <= top + 32:
            left, top, right, bottom = 0, 0, w, h
        frame = im.crop((left, top, right, bottom)).resize((w, h), Image.Resampling.LANCZOS)
        for op in rng.sample(ops, k=min(2, len(ops))):
            frame = op(frame)
        if idx % 2 == 1:
            frame = ImageEnhance.Sharpness(frame).enhance(1.15)
        dest = out_dir / f"{src.stem}_parecida_{idx + 1}.jpg"
        frame.save(dest, "JPEG", quality=92, optimize=True)
        paths.append(dest)
    return paths


def _openai_variants(src: Path, out_dir: Path, n: int = 3) -> list[Path] | None:
    """Optional OpenAI Images edit/variation if OPENAI_API_KEY is set."""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    try:
        import base64
        import json
        import urllib.request

        out_dir.mkdir(parents=True, exist_ok=True)
        # Prefer images/variations for a single reference photo
        boundary = "----similarphotosboundary"
        data = Path(src).read_bytes()
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="image"; filename="{src.name}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode() + data + (
            f"\r\n--{boundary}\r\n"
            f'Content-Disposition: form-data; name="n"\r\n\r\n{n}\r\n'
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="size"\r\n\r\n1024x1024\r\n'
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="response_format"\r\n\r\nb64_json\r\n'
            f"--{boundary}--\r\n"
        ).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/images/variations",
            data=body,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read().decode())
        paths: list[Path] = []
        for i, item in enumerate(payload.get("data", [])[:n], start=1):
            raw = base64.b64decode(item["b64_json"])
            dest = out_dir / f"{src.stem}_parecida_{i}.png"
            dest.write_bytes(raw)
            paths.append(dest)
        return paths if paths else None
    except Exception:
        return None


def generate_similar(src: Path, out_dir: Path, n: int = 3, prefer_api: bool = True) -> list[Path]:
    src = Path(src).expanduser().resolve()
    out_dir = Path(out_dir).expanduser().resolve()
    if not src.is_file():
        raise FileNotFoundError(src)
    if prefer_api:
        api = _openai_variants(src, out_dir, n=n)
        if api:
            return api
    return _local_variants(src, out_dir, n=n)
