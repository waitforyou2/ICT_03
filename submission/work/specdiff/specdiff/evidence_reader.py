from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Pattern

from .models import CodeEvidence


SOURCE_EXTENSIONS = {
    ".c", ".h", ".cc", ".cpp", ".cxx", ".hpp",
    ".py", ".java", ".go", ".rs", ".js", ".ts", ".cs",
    ".sh", ".ini", ".conf", ".yaml", ".yml", ".json",
}
EXCLUDED_DIRS = {
    ".git", ".codegraph", "node_modules", "build", "dist", "target",
    ".venv", "__pycache__", ".idea", ".vscode",
}
FUNCTION_LINE_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*\([^;]*$")
FUNCTION_DECL_RE = re.compile(
    r"^\s*(?:static\s+|inline\s+|extern\s+|const\s+)*"
    r"[A-Za-z_][\w\s\*]+\s+([A-Za-z_]\w*)\s*\([^;]*$"
)


@dataclass(slots=True)
class SourceFile:
    relative_path: str
    absolute_path: str
    text: str
    lines: list[str]


class EvidenceReader:
    def __init__(self, repo: str | Path, *, max_file_bytes: int = 2_000_000):
        self.repo = Path(repo).resolve()
        self.max_file_bytes = max_file_bytes
        self.files: dict[str, SourceFile] = {}
        self.skipped: list[str] = []

    def build(self) -> "EvidenceReader":
        for root, dirs, files in os.walk(self.repo):
            dirs[:] = sorted(d for d in dirs if d.lower() not in EXCLUDED_DIRS)
            for name in sorted(files):
                path = Path(root) / name
                if path.suffix.lower() not in SOURCE_EXTENSIONS:
                    continue
                try:
                    if path.stat().st_size > self.max_file_bytes:
                        self.skipped.append(str(path.relative_to(self.repo)))
                        continue
                    raw = path.read_bytes()
                except OSError:
                    self.skipped.append(str(path.relative_to(self.repo)))
                    continue
                if b"\x00" in raw[:4096]:
                    self.skipped.append(str(path.relative_to(self.repo)))
                    continue
                text = raw.decode("utf-8", errors="replace")
                relative = path.relative_to(self.repo).as_posix()
                self.files[relative] = SourceFile(
                    relative_path=relative,
                    absolute_path=str(path),
                    text=text,
                    lines=text.splitlines(),
                )
        return self

    def grep(self, pattern: str | Pattern[str]) -> Iterator[tuple[SourceFile, int, re.Match[str]]]:
        compiled = re.compile(pattern, re.IGNORECASE) if isinstance(pattern, str) else pattern
        for source in self.files.values():
            for line_number, line in enumerate(source.lines, start=1):
                match = compiled.search(line)
                if match:
                    yield source, line_number, match

    def search_text(
        self, pattern: str | Pattern[str]
    ) -> Iterator[tuple[SourceFile, re.Match[str]]]:
        compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE) if isinstance(pattern, str) else pattern
        for source in self.files.values():
            match = compiled.search(source.text)
            while match:
                yield source, match
                match = compiled.search(source.text, match.end())

    def line_at_offset(self, relative_path: str, offset: int) -> int:
        return self.files[relative_path].text.count("\n", 0, offset) + 1

    def occurrences(self, token: str, *, case_sensitive: bool = True) -> list[tuple[SourceFile, int]]:
        result: list[tuple[SourceFile, int]] = []
        needle = token if case_sensitive else token.lower()
        for source in self.files.values():
            for line_number, line in enumerate(source.lines, start=1):
                haystack = line if case_sensitive else line.lower()
                if needle in haystack:
                    result.append((source, line_number))
        return result

    def context(self, relative_path: str, line: int, before: int = 3, after: int = 5) -> str:
        source = self.files[relative_path]
        start = max(1, line - before)
        end = min(len(source.lines), line + after)
        return "\n".join(
            f"{number}:{source.lines[number - 1]}" for number in range(start, end + 1)
        )

    def evidence(
        self,
        relative_path: str,
        line: int,
        purpose: str,
        *,
        before: int = 2,
        after: int = 4,
    ) -> CodeEvidence:
        source = self.files[relative_path]
        start = max(1, line - before)
        end = min(len(source.lines), line + after)
        return CodeEvidence(
            path=relative_path,
            line_start=start,
            line_end=end,
            symbol=self.enclosing_symbol(relative_path, line),
            excerpt="\n".join(
                f"{number}:{source.lines[number - 1]}" for number in range(start, end + 1)
            ),
            purpose=purpose,
        )

    def enclosing_symbol(self, relative_path: str, line: int) -> str:
        source = self.files[relative_path]
        lower = max(0, line - 2000)

        def opens_body(index: int) -> bool:
            tail = "\n".join(source.lines[index:min(len(source.lines), index + 16)])
            brace, semicolon = tail.find("{"), tail.find(";")
            return brace >= 0 and (semicolon < 0 or brace < semicolon)

        for index in range(min(line - 1, len(source.lines) - 1), lower - 1, -1):
            text = source.lines[index]
            match = FUNCTION_DECL_RE.match(text)
            if match and opens_body(index):
                return match.group(1)
            match = FUNCTION_LINE_RE.match(text)
            if (
                match
                and text == text.lstrip()
                and not match.group(1).isupper()
                and opens_body(index)
            ):
                return match.group(1)
        return "<file-scope>"

    def verify_evidence(self, evidence: CodeEvidence) -> bool:
        source = self.files.get(evidence.path)
        if source is None or evidence.line_start < 1:
            return False
        try:
            current_text = Path(source.absolute_path).read_bytes().decode("utf-8", errors="replace")
        except OSError:
            return False
        current_lines = current_text.splitlines()
        if evidence.line_end > len(current_lines):
            return False
        current = "\n".join(
            f"{number}:{current_lines[number - 1]}"
            for number in range(evidence.line_start, evidence.line_end + 1)
        )
        return current == evidence.excerpt
