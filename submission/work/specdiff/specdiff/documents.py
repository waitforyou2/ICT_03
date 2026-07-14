from __future__ import annotations

import html
import re
import urllib.request
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable

from .models import Requirement, stable_id


URL_RE = re.compile(r"https?://[^\s)\]>]+")
RFC_RE = re.compile(r"(?:rfc-editor\.org/rfc/)?rfc(\d+)", re.IGNORECASE)
SECTION_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\.\s+(.+?)\s*$")
NORMATIVE_RE = re.compile(
    r"\b(MUST NOT|SHALL NOT|SHOULD NOT|MUST|REQUIRED|SHALL|SHOULD|RECOMMENDED|MAY|OPTIONAL)\b"
)
BEHAVIOR_RE = re.compile(
    r"\b(type\s*=\s*(?:decimal\s+)?\d+|client/server protocol|"
    r"not implemented|not support|configured|configuration|extension header|"
    r"multicast listener|neighbor advertisement|proxy advertisement|random time|valid options)\b",
    re.IGNORECASE,
)


@dataclass(slots=True)
class Document:
    name: str
    path: str
    text: str


def _read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _html_to_text(value: str) -> str:
    value = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", value)
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"[ \t]+", " ", value)


def _canonical_rfc_url(url: str) -> tuple[str, str] | None:
    match = RFC_RE.search(url)
    if not match:
        return None
    number = match.group(1)
    return number, f"https://www.rfc-editor.org/rfc/rfc{number}.txt"


def _download(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "SpecDiff-Reviewer/0.1 (+offline-cache)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace")


def _candidate_local_files(input_path: Path) -> Iterable[Path]:
    if input_path.is_file():
        yield input_path
        return
    excluded = {"issues", ".git", ".codegraph", "node_modules", "build", "dist"}
    for path in sorted(input_path.rglob("*")):
        if not path.is_file() or any(part.lower() in excluded for part in path.parts):
            continue
        if path.suffix.lower() in {".md", ".txt", ".rst", ".html", ".htm"}:
            yield path


def load_documents(
    input_path: str | Path,
    cache_dir: str | Path,
    *,
    allow_network: bool = True,
) -> tuple[list[Document], list[str]]:
    source = Path(input_path).resolve()
    cache = Path(cache_dir).resolve()
    cache.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    documents: list[Document] = []
    urls: set[str] = set()

    for path in _candidate_local_files(source):
        text = _read_text(path)
        if path.suffix.lower() in {".html", ".htm"}:
            text = _html_to_text(text)
        documents.append(Document(path.stem, str(path), text))
        urls.update(URL_RE.findall(text))

    for url in sorted(urls):
        canonical = _canonical_rfc_url(url)
        if canonical:
            number, fetch_url = canonical
            cache_path = cache / f"rfc{number}.txt"
            name = f"RFC {number}"
        else:
            # Links inside design documents are often navigation or citations rather
            # than specifications.  Fetch RFC citations deterministically; callers
            # can still pass any non-RFC document as a local file.
            continue

        if cache_path.exists():
            text = _read_text(cache_path)
        elif allow_network:
            try:
                text = _download(fetch_url)
                cache_path.write_text(text, encoding="utf-8")
            except Exception as exc:  # noqa: BLE001 - preserve audit progress
                warnings.append(f"document download failed: {fetch_url}: {exc}")
                continue
        else:
            warnings.append(f"offline document cache missing: {fetch_url}")
            continue
        documents.append(Document(name, str(cache_path), text))

    unique: dict[tuple[str, str], Document] = {}
    for document in documents:
        key = (document.name, sha256(document.text.encode("utf-8")).hexdigest())
        unique[key] = document
    return list(unique.values()), warnings


def _strength(text: str) -> str:
    upper = text.upper()
    if "MUST NOT" in upper or "SHALL NOT" in upper:
        return "must_not"
    if re.search(r"\b(MUST|REQUIRED|SHALL)\b", text):
        return "must"
    if re.search(r"\b(SHOULD NOT)\b", text):
        return "should_not"
    if re.search(r"\b(SHOULD|RECOMMENDED)\b", text):
        return "should"
    if re.search(r"\b(MAY|OPTIONAL)\b", text):
        return "may"
    if re.search(r"\bshould\b", text):
        return "recommendation"
    return "informative"


def _rfc_paragraphs(document: Document) -> list[tuple[str, int, str]]:
    current_section = ""
    buffer: list[str] = []
    buffer_line = 1
    result: list[tuple[str, int, str]] = []

    def flush() -> None:
        nonlocal buffer
        if not buffer:
            return
        paragraph = re.sub(r"\s+", " ", " ".join(buffer)).strip()
        if len(paragraph) >= 35:
            result.append((current_section, buffer_line, paragraph))
        buffer = []

    for line_number, raw_line in enumerate(document.text.splitlines(), start=1):
        line = raw_line.rstrip()
        section_match = SECTION_RE.match(line)
        if section_match and len(section_match.group(2)) < 160:
            flush()
            current_section = section_match.group(1)
            continue
        stripped = line.strip()
        if (
            not stripped
            or stripped == "\f"
            or re.search(r"\[Page\s+\d+\]", stripped)
            or re.match(r"RFC\s+\d+\s+", stripped)
        ):
            flush()
            continue
        if not buffer:
            buffer_line = line_number
        buffer.append(stripped)
    flush()
    return result


def extract_requirements(documents: Iterable[Document]) -> list[Requirement]:
    requirements: list[Requirement] = []
    seen: set[str] = set()
    for document in documents:
        for section, line, paragraph in _rfc_paragraphs(document):
            if not (NORMATIVE_RE.search(paragraph) or BEHAVIOR_RE.search(paragraph)):
                continue
            normalized = re.sub(r"\s+", " ", paragraph).strip()
            digest = sha256(normalized.lower().encode("utf-8")).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            requirements.append(
                Requirement(
                    id=stable_id("req", document.name, section, normalized),
                    document=document.name,
                    source_path=document.path,
                    section=section or "unsectioned",
                    text=normalized,
                    strength=_strength(normalized),
                    line=line,
                )
            )
    return requirements
