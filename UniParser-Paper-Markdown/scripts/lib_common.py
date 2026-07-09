"""Shared helpers for the UniParser paper Markdown skill CLI scripts."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DEFAULT_HOST = "https://uniparser.dp.tech"
INSTALL_CMD = "git+https://github.com/dptech-corp/UniParser-Tools.git"
SKILL_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = SKILL_ROOT / "config.json"

POLL_INTERVAL_SEC = 3
POLL_TIMEOUT_SEC = 1800

PENDING_STATUSES = frozenset({"undefined", "waiting", "processing"})
API_KEY_CONFIG_FIELDS = ("api_key", "UNIPARSER_API_KEY", "uniparser_api_key")
API_KEY_PLACEHOLDERS = frozenset({"", "your-api-key", "your_api_key", "replace-me", "replace_me"})

DATA_IMAGE_MD_RE = re.compile(
    r"!\[([^\]]*)\]\(data:image/([a-zA-Z0-9.+-]+);base64,([A-Za-z0-9+/=\r\n]+)\)",
    re.IGNORECASE,
)
DATA_IMAGE_HTML_RE = re.compile(
    r"<img\b(?P<attrs_before>[^>]*)\bsrc=[\"']data:image/(?P<mime>[a-zA-Z0-9.+-]+);base64,(?P<payload>[^\"']+)[\"'](?P<attrs_after>[^>]*)>",
    re.IGNORECASE,
)
ALT_ATTR_RE = re.compile(r"\balt=[\"']([^\"']*)[\"']", re.IGNORECASE)


def emit_json_stderr(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)


def config_error(message: str) -> int:
    emit_json_stderr({"ok": False, "error": {"code": "CONFIG_ERROR", "message": message}})
    return 1


def dir_exists_error(output_dir: Path) -> int:
    emit_json_stderr(
        {
            "ok": False,
            "error": {
                "code": "DIR_EXISTS",
                "message": (
                    f"Output directory already exists: {output_dir}. "
                    "Ask the user whether to continue parsing. "
                    "If they agree, re-run the same command with --overwrite."
                ),
                "output_dir": str(output_dir),
            },
        }
    )
    return 1


def parse_error(stage: str, result: dict) -> int:
    emit_json_stderr(
        {
            "ok": False,
            "error": {
                "code": "PARSE_ERROR",
                "message": result.get("description") or result.get("message") or str(result),
                "stage": stage,
            },
            "token": result.get("token"),
        }
    )
    return 1


def _usable_api_key(value: Any) -> str | None:
    if value is None:
        return None
    key = str(value).strip()
    if key.lower() in API_KEY_PLACEHOLDERS:
        return None
    return key or None


def _load_local_config() -> tuple[dict[str, Any], str | None]:
    if not CONFIG_PATH.exists():
        return {}, None
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, f"Invalid JSON in local config file {CONFIG_PATH}: {exc}"
    if not isinstance(data, dict):
        return {}, f"Local config file {CONFIG_PATH} must contain a JSON object."
    return data, None


def resolve_api_key() -> tuple[str | None, str | None, str | None]:
    env_key = _usable_api_key(os.getenv("UNIPARSER_API_KEY"))
    if env_key:
        return env_key, "environment variable UNIPARSER_API_KEY", None

    config, error = _load_local_config()
    if error:
        return None, None, error
    for field in API_KEY_CONFIG_FIELDS:
        config_key = _usable_api_key(config.get(field))
        if config_key:
            return config_key, f"local config {CONFIG_PATH.name}:{field}", None
    return None, None, None


def get_api_key() -> str | None:
    key, _source, _error = resolve_api_key()
    return key


def require_api_key() -> str:
    key = get_api_key()
    if not key:
        raise RuntimeError("API key is missing; run_startup_checks should be called before require_api_key().")
    return key


def check_api_key() -> int | None:
    key, _source, error = resolve_api_key()
    if error:
        return config_error(error)
    if key:
        return None
    return config_error(
        "UNIPARSER_API_KEY is not set and local config.json has no usable api_key. "
        "Set the environment variable first, or fill this skill's config.json as a fallback."
    )


def check_uniparser_installed() -> int | None:
    try:
        import uniparser_tools  # noqa: F401
    except ImportError:
        return config_error(
            "uniparser_tools is not installed. Run once: "
            f'pip install "{INSTALL_CMD}"'
        )
    return None


def run_startup_checks() -> int | None:
    """API key + package presence. Returns exit code if checks fail."""
    code = check_api_key()
    if code is not None:
        return code
    return check_uniparser_installed()


def source_stem_from_path(path: Path) -> str:
    return path.stem or "document"


def source_stem_from_url(url: str) -> str:
    """Last URL path segment; strip only known doc extensions, not arXiv ID dots."""
    segment = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
    if not segment:
        return "url_document"
    lower = segment.lower()
    for ext in (".pdf", ".png", ".jpg", ".jpeg", ".webp"):
        if lower.endswith(ext):
            segment = segment[: -len(ext)]
            break
    return segment or "url_document"


def default_output_dir(source_stem: str) -> Path:
    return (Path.home() / "Uni-Parser-Paper-Markdown" / source_stem).expanduser().resolve()


def resolve_fetch_target(
    *,
    token: str | None,
    file_path: str | None,
    image_path: str | None,
    pdf_url: str | None,
    client,
) -> tuple[str, str] | int:
    """Resolve task token and source_stem for fetch_by_token. Returns exit code on error."""
    provided = sum(1 for value in (token, file_path, image_path, pdf_url) if value is not None)
    if provided != 1:
        return config_error("Provide exactly one of --token, --file-path, --image-path, or --pdf-url.")

    if token is not None:
        resolved = token.strip()
        if not resolved:
            return config_error("Token must not be empty.")
        return resolved, f"token_{resolved[:8]}"

    if file_path is not None:
        path = Path(file_path).expanduser().resolve()
        if not path.is_file():
            return config_error(f"File not found: {path}")
        task_id = str(path)
        return client.to_token(task_id), source_stem_from_path(path)

    if image_path is not None:
        path = Path(image_path).expanduser().resolve()
        if not path.is_file():
            return config_error(f"Image not found: {path}")
        task_id = str(path)
        return client.to_token(task_id), source_stem_from_path(path)

    task_id = pdf_url.strip()
    if not task_id:
        return config_error("PDF URL must not be empty.")
    return client.to_token(task_id), source_stem_from_url(task_id)


def resolve_output_dir(
    source_stem: str,
    output_dir: str | None,
    *,
    overwrite: bool,
) -> tuple[Path | None, int | None]:
    out = Path(output_dir).expanduser().resolve() if output_dir else default_output_dir(source_stem)
    if out.exists() and not overwrite:
        return None, dir_exists_error(out)
    if out.exists() and overwrite:
        shutil.rmtree(out)
    return out, None


def scientific_paper_trigger_kwargs(*, sync: bool = True) -> dict:
    from uniparser_tools.common.constant import ParseMode, ParseModeTextual

    return {
        "sync": sync,
        "textual": ParseModeTextual.OCRHighQuality,
        "equation": ParseMode.OCRHighQuality,
        "table": ParseMode.OCRHighQuality,
        "chart": ParseMode.DumpBase64,
        "figure": ParseMode.DumpBase64,
        "expression": ParseMode.DumpBase64,
        "molecule": ParseMode.OCRFast,
    }


def poll_until_success(client, token: str) -> dict | int:
    """Poll get_result until status is success. Returns result dict or exit code."""
    deadline = time.time() + POLL_TIMEOUT_SEC
    last: dict[str, Any] = {}

    while time.time() < deadline:
        last = client.get_result(
            token,
            content=False,
            objects=False,
            pages_dict=False,
            pages_tree=False,
        )
        status = last.get("status")
        if status == "success":
            return last
        if status == "error":
            return parse_error("get_result_poll", last)
        if status in PENDING_STATUSES or status is None:
            time.sleep(POLL_INTERVAL_SEC)
            continue
        return parse_error("get_result_poll", last)

    return parse_error(
        "get_result_poll",
        {
            "status": "error",
            "description": f"Timed out after {POLL_TIMEOUT_SEC}s waiting for parsing to finish.",
            "token": token,
            "last_status": last.get("status"),
        },
    )


def fetch_pages_tree(client, token: str) -> dict:
    return client.get_result(token, pages_tree=True, objects=False)


def fetch_markdown(client, token: str) -> dict:
    from uniparser_tools.common.constant import FormatFlag

    return client.get_formatted(
        token,
        content=True,
        textual=FormatFlag.Markdown,
        table=FormatFlag.Markdown,
        molecule=FormatFlag.Markdown,
        chart=FormatFlag.Markdown,
        figure=FormatFlag.Markdown,
        expression=FormatFlag.Markdown,
        equation=FormatFlag.Latex,
    )


def _image_extension(mime_subtype: str) -> str:
    subtype = mime_subtype.lower().split(";", 1)[0]
    if subtype == "jpeg":
        return "jpg"
    if subtype == "svg+xml":
        return "svg"
    return re.sub(r"[^a-z0-9]+", "", subtype) or "png"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip().lower()).strip("-._")
    return (slug or "image")[:40]


def materialize_markdown_images(markdown: str, images_dir: Path) -> tuple[str, dict[str, Any]]:
    """Write data-URI images into images_dir and replace Markdown links with relative paths."""
    images_dir.mkdir(parents=True, exist_ok=True)
    digest_to_name: dict[str, str] = {}
    errors: list[str] = []
    counter = 0

    def write_image(alt: str, mime_subtype: str, payload: str) -> str | None:
        nonlocal counter
        compact_payload = re.sub(r"\s+", "", payload)
        try:
            data = base64.b64decode(compact_payload, validate=True)
        except (binascii.Error, ValueError) as exc:
            errors.append(f"Failed to decode {alt or mime_subtype} image: {exc}")
            return None

        digest = hashlib.sha256(data).hexdigest()[:12]
        if digest not in digest_to_name:
            counter += 1
            ext = _image_extension(mime_subtype)
            base = _slug(alt or mime_subtype)
            filename = f"{base}_{counter:04d}_{digest}.{ext}"
            (images_dir / filename).write_bytes(data)
            digest_to_name[digest] = filename
        return f"images/{digest_to_name[digest]}"

    def replace_markdown_image(match: re.Match[str]) -> str:
        alt, mime_subtype, payload = match.groups()
        rel_path = write_image(alt, mime_subtype, payload)
        if not rel_path:
            return match.group(0)
        return f"![{alt}]({rel_path})"

    def replace_html_image(match: re.Match[str]) -> str:
        attrs = f"{match.group('attrs_before')} {match.group('attrs_after')}"
        alt_match = ALT_ATTR_RE.search(attrs)
        alt = alt_match.group(1) if alt_match else "image"
        rel_path = write_image(alt, match.group("mime"), match.group("payload"))
        if not rel_path:
            return match.group(0)
        return f"![{alt}]({rel_path})"

    markdown = DATA_IMAGE_MD_RE.sub(replace_markdown_image, markdown)
    markdown = DATA_IMAGE_HTML_RE.sub(replace_html_image, markdown)
    return markdown, {
        "image_count": len(digest_to_name),
        "images_dir": str(images_dir),
        "image_errors": errors,
    }


def save_parse_results(
    *,
    out_dir: Path,
    source_stem: str,
    pages_tree: dict,
    formatted: dict,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = source_stem or "document"

    pages_tree_path = out_dir / "pages_tree.json"
    pages_tree_path.write_text(
        json.dumps(pages_tree, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    md_path = out_dir / f"{stem}.md"
    raw_content = formatted.get("content", "")
    content, image_summary = materialize_markdown_images(raw_content, out_dir / "images")
    md_path.write_text(content, encoding="utf-8")

    meta = {k: v for k, v in formatted.items() if k != "content"}
    meta["markdown_image_export"] = image_summary
    (out_dir / "formatted_meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    return {
        "ok": True,
        "output_dir": str(out_dir),
        "pages_tree_path": str(pages_tree_path),
        "markdown_path": str(md_path),
        "images_dir": image_summary["images_dir"],
        "image_count": image_summary["image_count"],
        "image_errors": image_summary["image_errors"],
        "content_chars": len(content),
    }


def print_success(summary: dict) -> None:
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Pages tree saved to: {summary['pages_tree_path']}", file=sys.stderr)
    print(f"Markdown saved to: {summary['markdown_path']}", file=sys.stderr)
    print(f"Images saved to: {summary['images_dir']}", file=sys.stderr)
    print(f"Output directory: {summary['output_dir']}", file=sys.stderr)
