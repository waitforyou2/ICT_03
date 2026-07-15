#!/usr/bin/env python3
"""Extract normative requirements and implementation-difference candidates.

The output is candidate evidence, not an answer key. Every candidate must still
pass the skill's evidence gate and CodeGraph counterevidence search.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


EXCLUDED_PARTS = {
    ".git", ".codegraph", "target", "node_modules", "maven-repo", "validation"
}
REQUIREMENT_MARKERS = re.compile(
    r"必须|不得|禁止|不可|只允许|应当|需要|统一|默认|上限|下限|固定为|"
    r"must\b|must not\b|shall\b|should\b|required\b|forbidden\b",
    re.IGNORECASE,
)


@dataclass
class Requirement:
    id: str
    path: str
    line: int
    strength: str
    text: str


@dataclass
class Candidate:
    id: str
    rule: str
    title: str
    classification: str
    severity: str
    confidence: int
    path: str
    line_start: int
    line_end: int
    symbol_hint: str
    excerpt: str
    actual_behavior: str
    design_hints: list[dict]
    status: str = "candidate"


@dataclass(frozen=True)
class RegexRule:
    name: str
    title: str
    path_pattern: str
    content_pattern: str
    classification: str
    severity: str
    confidence: int
    actual_behavior: str
    design_keywords: tuple[str, ...]
    flags: int = re.IGNORECASE


REGEX_RULES = (
    RegexRule(
        "money-half-down", "Monetary rounding is not HALF_UP", r"MonetaryUtil\.java$",
        r"RoundingMode\.HALF_DOWN", "contract_contradiction", "high", 99,
        "A shared monetary utility rounds midpoint values down instead of using the required HALF_UP rule.",
        ("HALF_UP", "金额", "舍入"),
    ),
    RegexRule(
        "forbidden-reset-bootstrap", "Forbidden reset or bootstrap route is exposed",
        r"(?:Controller|SecurityConfig)\.java$", r"/[^\"']*(?:reset-sandbox|bootstrap-admin)",
        "forbidden_extra_behavior", "critical", 99,
        "Production security or controller code exposes a test reset/bootstrap route.",
        ("reset", "bootstrap", "不得", "隔离"),
    ),
    RegexRule(
        "fake-stock", "Product stock uses a placeholder value", r"StockInfoFetcher\.java$",
        r"StockSummaryDto\s*\(\s*999\s*,", "contract_contradiction", "high", 99,
        "Product detail returns a fixed stock summary instead of querying inventory.",
        ("InventoryQueryService", "库存摘要", "不得直接"),
    ),
    RegexRule(
        "cart-placeholder-pricing", "Cart pricing contains a required-behavior placeholder",
        r"CartService\.java$", r"not yet integrated|placeholder\s*\(requires\s+PromotionCalculationService",
        "missing_behavior", "high", 98,
        "Cart estimate explicitly omits promotion and points calculation.",
        ("价格预估", "PromotionCalculationService", "积分"),
    ),
    RegexRule(
        "cart-jpa-storage", "Temporary cart is persisted through JPA repositories",
        r"ecommerce-cart/.*/CartService\.java$", r"import\s+com\.ecommerce\.cart\.repository\.(?:Cart|CartItem)Repository",
        "architecture_boundary", "high", 99,
        "CartService persists temporary cart state through repositories although the contract assigns it to Caffeine.",
        ("Caffeine", "购物车", "不得落库"),
    ),
    RegexRule(
        "product-search-default", "Public product search includes non-shelf products by default",
        r"ProductSearchRequest\.java$", r"onlyOnShelf\s*=\s*false",
        "contract_contradiction", "high", 98,
        "The default search request does not restrict results to ON_SHELF products.",
        ("默认", "ON_SHELF", "商品搜索"),
    ),
    RegexRule(
        "refund-fixed-fee", "Refund subtracts an undocumented fixed fee", r"RefundCalculator\.java$",
        r"subtract\s*\(\s*baseRefund\s*,\s*BigDecimal\.ONE\s*\)",
        "contract_contradiction", "high", 99,
        "Refund calculation applies the configured rate and then subtracts an extra fixed amount.",
        ("退款金额", "手续费率", "不得额外"),
    ),
    RegexRule(
        "sensitive-word-equality", "Sensitive-word detection uses whole-string equality",
        r"SensitiveWordFilter\.java$", r"getWord\s*\(\s*\)\.equals\s*\(",
        "contract_contradiction", "medium", 98,
        "Sensitive content is recognized only when the entire review equals one sensitive word.",
        ("敏感词", "包含匹配", "完全相等"),
    ),
    RegexRule(
        "order-validation-exception", "Order amount validation throws a standard exception",
        r"OrderValidator\.java$", r"throw\s+new\s+IllegalArgumentException",
        "contract_contradiction", "high", 99,
        "Invalid order amount throws IllegalArgumentException instead of OrderValidationException.",
        ("OrderValidationException", "IllegalArgumentException", "订单金额"),
    ),
    RegexRule(
        "registration-active", "Registration bypasses pending activation",
        r"UserRegisterService\.java$", r"setStatus\s*\(\s*UserStatus\.ACTIVE\s*\)",
        "workflow_state", "high", 99,
        "The registration path activates a user immediately instead of creating PENDING_ACTIVATION.",
        ("PENDING_ACTIVATION", "注册流程", "激活"),
    ),
    RegexRule(
        "inventory-duplicate-product", "Inventory duplicates product-owned model",
        r"ecommerce-inventory/.*/(?:Product|ProductRepository)\.java$", r"(?:class|interface)\s+Product(?:Repository)?\b",
        "architecture_boundary", "high", 98,
        "Inventory declares a local Product entity or repository instead of using ProductQueryService.",
        ("ProductQueryService", "库存服务", "商品主数据"),
    ),
    RegexRule(
        "generic-required-placeholder", "Required production path contains an implementation admission",
        r"src/main/.*\.java$", r"\bTODO\b|\bFIXME\b|not yet integrated|not implemented|\bplaceholder\b",
        "missing_behavior", "medium", 78,
        "Production source contains an admission that may correspond to missing required behavior.",
        ("必须", "实现", "流程"),
    ),
)


def stable_id(prefix: str, *parts: object) -> str:
    raw = "\x1f".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


def strength(text: str) -> str:
    lowered = text.lower()
    if re.search(r"不得|禁止|不可|must not\b|forbidden\b", lowered):
        return "forbidden"
    if re.search(r"必须|应当|需要|must\b|shall\b|required\b", lowered):
        return "mandatory"
    if re.search(r"默认|固定为|上限|下限", lowered):
        return "constraint"
    if re.search(r"should\b|建议|优先", lowered):
        return "recommended"
    return "normative"


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def document_files(assets: Path) -> list[Path]:
    files = []
    for name in ("README.md", "PLATFORM.md"):
        path = assets / name
        if path.is_file():
            files.append(path)
    design = assets / "design-docs"
    if design.is_dir():
        files.extend(sorted(design.rglob("*.md")))
    return files


def extract_requirements(assets: Path) -> list[Requirement]:
    output: list[Requirement] = []
    for path in document_files(assets):
        in_fence = False
        for number, raw in enumerate(read_text(path).splitlines(), 1):
            line = raw.strip()
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or not line or line.startswith("#"):
                continue
            if not REQUIREMENT_MARKERS.search(line):
                continue
            source = relative(path, assets)
            output.append(
                Requirement(
                    id=stable_id("req", source, number, line),
                    path=source,
                    line=number,
                    strength=strength(line),
                    text=line,
                )
            )
    return output


def source_files(code: Path) -> Iterable[Path]:
    for path in code.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".java", ".yml", ".yaml", ".xml"}:
            continue
        if any(part in EXCLUDED_PARTS for part in path.relative_to(code).parts):
            continue
        yield path


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def excerpt(text: str, start_line: int, end_line: int | None = None, radius: int = 2) -> str:
    lines = text.splitlines()
    end_line = end_line or start_line
    first = max(1, start_line - radius)
    last = min(len(lines), end_line + radius)
    return "\n".join(f"{index}: {lines[index - 1]}" for index in range(first, last + 1))


def design_hints(requirements: list[Requirement], keywords: tuple[str, ...]) -> list[dict]:
    ranked = []
    for requirement in requirements:
        lowered = requirement.text.lower()
        score = sum(1 for keyword in keywords if keyword.lower() in lowered)
        if score:
            ranked.append((score, requirement))
    ranked.sort(key=lambda item: (-item[0], item[1].path, item[1].line))
    return [asdict(item[1]) for item in ranked[:3]]


def add_candidate(
    output: list[Candidate], rule: RegexRule, path: Path, code: Path,
    text: str, start: int, end: int, requirements: list[Requirement],
) -> None:
    start_line = line_number(text, start)
    end_line = line_number(text, end)
    source = relative(path, code)
    output.append(
        Candidate(
            id=stable_id("finding", rule.name, source, start_line),
            rule=rule.name,
            title=rule.title,
            classification=rule.classification,
            severity=rule.severity,
            confidence=rule.confidence,
            path=source,
            line_start=start_line,
            line_end=end_line,
            symbol_hint=path.stem,
            excerpt=excerpt(text, start_line, end_line),
            actual_behavior=rule.actual_behavior,
            design_hints=design_hints(requirements, rule.design_keywords),
        )
    )


def run_regex_rules(code: Path, requirements: list[Requirement]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for path in source_files(code):
        source = relative(path, code)
        text = read_text(path)
        normalized_source = source.replace("\\", "/")
        for rule in REGEX_RULES:
            if not re.search(rule.path_pattern, normalized_source, re.IGNORECASE):
                continue
            for match in re.finditer(rule.content_pattern, text, rule.flags | re.MULTILINE):
                add_candidate(candidates, rule, path, code, text, match.start(), match.end(), requirements)
    return candidates


def synthetic_rule(
    name: str, title: str, classification: str, severity: str, confidence: int,
    behavior: str, keywords: tuple[str, ...], path_pattern: str = r".*",
) -> RegexRule:
    return RegexRule(
        name, title, path_pattern, r"", classification, severity, confidence,
        behavior, keywords,
    )


def add_special_candidate(
    output: list[Candidate], rule: RegexRule, path: Path, code: Path,
    text: str, anchor: str, requirements: list[Requirement],
) -> None:
    offset = text.find(anchor)
    if offset < 0:
        offset = 0
    add_candidate(output, rule, path, code, text, offset, offset + max(1, len(anchor)), requirements)


def run_special_rules(code: Path, requirements: list[Requirement]) -> list[Candidate]:
    output: list[Candidate] = []

    payment = next(code.rglob("PaymentValidator.java"), None)
    if payment:
        text = read_text(payment)
        if "getPayableAmount" not in text:
            rule = synthetic_rule(
                "payment-exact-amount", "Payment does not compare against order payable amount",
                "contract_contradiction", "critical", 98,
                "Payment validation checks positivity and method but not exact equality with the order payable amount.",
                ("全额支付", "应付金额", "小于或大于"),
            )
            add_special_candidate(output, rule, payment, code, text, "public void validate", requirements)

    state_machine = next(code.rglob("OrderStateMachine.java"), None)
    if state_machine:
        text = read_text(state_machine)
        paid = re.search(
            r"allowedTransitions\.put\s*\(\s*OrderStatus\.PAID[\s\S]{0,260}?OrderStatus\.CANCELLED",
            text,
        )
        if paid:
            rule = synthetic_rule(
                "paid-direct-cancel", "Paid order can transition directly to CANCELLED",
                "workflow_state", "critical", 99,
                "The order state machine permits a paid order to bypass cancellation review.",
                ("PAID", "CANCEL_REVIEWING", "不得直接"),
            )
            add_candidate(output, rule, state_machine, code, text, paid.start(), paid.end(), requirements)

    shipment = next(code.rglob("ShipmentService.java"), None)
    if shipment:
        text = read_text(shipment)
        create_end = text.find("public void pick")
        create_region = text[:create_end] if create_end > 0 else text
        outbound = re.search(r"setStatus\s*\(\s*ShipmentStatus\.OUTBOUND\s*\)", create_region)
        if outbound:
            rule = synthetic_rule(
                "shipment-starts-outbound", "Shipment is created in OUTBOUND state",
                "workflow_state", "critical", 99,
                "Shipment creation skips CREATED, PICKING, and LABEL_PRINTED states.",
                ("CREATED", "PICKING", "LABEL_PRINTED", "不得跳过"),
            )
            add_candidate(output, rule, shipment, code, text, outbound.start(), outbound.end(), requirements)

    promotion = next(code.rglob("PromotionCalculationService.java"), None)
    if promotion:
        text = read_text(promotion)
        member = text.find("memberDiscount")
        full = text.find("fullReductionDiscount")
        if 0 <= member < full:
            rule = synthetic_rule(
                "promotion-stack-order", "Promotion stacking order starts with member discount",
                "contract_contradiction", "high", 92,
                "Promotion calculation appears to apply member discount before full reduction and coupon.",
                ("满减", "优惠券", "会员", "顺序"),
            )
            add_special_candidate(output, rule, promotion, code, text, "memberDiscount", requirements)

    # Generic cross-module Repository import detector.
    import_pattern = re.compile(
        r"^import\s+com\.ecommerce\.([^.]+)\.repository\.[\w.]*Repository\s*;",
        re.MULTILINE,
    )
    for path in source_files(code):
        if path.suffix.lower() != ".java":
            continue
        source = relative(path, code)
        module = source.split("/", 1)[0].removeprefix("ecommerce-")
        text = read_text(path)
        for match in import_pattern.finditer(text):
            owner = match.group(1)
            if owner == module:
                continue
            rule = synthetic_rule(
                "cross-module-repository", "Module imports another module's Repository",
                "architecture_boundary", "high", 96,
                f"Module {module} imports a Repository owned by module {owner}.",
                ("禁止跨模块", "Repository", "QueryService"),
            )
            add_candidate(output, rule, path, code, text, match.start(), match.end(), requirements)
    return output


def deduplicate(candidates: list[Candidate]) -> list[Candidate]:
    seen = set()
    output = []
    for candidate in sorted(candidates, key=lambda item: (item.path, item.line_start, item.rule)):
        key = (candidate.rule, candidate.path, candidate.line_start)
        if key in seen:
            continue
        seen.add(key)
        output.append(candidate)
    return output


def markdown(payload: dict) -> str:
    lines = [
        "# Contract Scan Candidates",
        "",
        "> Candidates are leads. Apply the evidence gate and CodeGraph counterevidence before accepting a Finding.",
        "",
        f"Requirements extracted: {payload['summary']['requirements']}",
        f"Candidates: {payload['summary']['candidates']}",
        "",
        "| ID | Severity | Rule | Location | Title |",
        "|---|---|---|---|---|",
    ]
    for item in payload["candidates"]:
        location = f"{item['path']}:{item['line_start']}"
        title = item["title"].replace("|", "\\|")
        lines.append(
            f"| `{item['id']}` | {item['severity']} | `{item['rule']}` | `{location}` | {title} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", required=True, type=Path)
    parser.add_argument("--code", required=True, type=Path)
    parser.add_argument("--json", required=True, type=Path)
    parser.add_argument("--markdown", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assets = args.assets.resolve()
    code = args.code.resolve()
    if not assets.is_dir() or not code.is_dir():
        raise SystemExit("Both --assets and --code must be existing directories")

    requirements = extract_requirements(assets)
    candidates = deduplicate(
        run_regex_rules(code, requirements) + run_special_rules(code, requirements)
    )
    payload = {
        "schema_version": "2.0-candidates",
        "asset_root": str(assets),
        "code_root": str(code),
        "summary": {
            "requirements": len(requirements),
            "candidates": len(candidates),
            "notice": "Candidates require evidence-gate and counterevidence review.",
        },
        "requirements": [asdict(item) for item in requirements],
        "candidates": [asdict(item) for item in candidates],
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(markdown(payload), encoding="utf-8")
    print(
        f"CONTRACT_SCAN requirements={len(requirements)} candidates={len(candidates)} "
        f"json={args.json} markdown={args.markdown}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
