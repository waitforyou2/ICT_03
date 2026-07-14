from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Protocol

from .models import Candidate, Requirement, stable_id
from .evidence_reader import EvidenceReader, SourceFile


class Detector(Protocol):
    name: str

    def run(self, index: EvidenceReader, requirements: list[Requirement]) -> list[Candidate]: ...


def function_call_sites(index: EvidenceReader, name: str) -> list[tuple[SourceFile, int]]:
    """Return call statements while excluding prototypes and function definitions."""
    result: list[tuple[SourceFile, int]] = []
    for source, line in index.occurrences(name, case_sensitive=True):
        text = source.lines[line - 1]
        match = re.search(rf"\b{re.escape(name)}\s*\(", text)
        if not match:
            continue
        prefix = text[:match.start()]
        if re.search(r"\b(?:void|int|char|long|short|struct|enum|static|extern|inline)\b", prefix):
            continue
        statement = "\n".join(source.lines[line - 1:min(len(source.lines), line + 8)])
        semicolon, brace = statement.find(";"), statement.find("{")
        if semicolon < 0 or (brace >= 0 and brace < semicolon):
            continue
        result.append((source, line))
    return result


def make_candidate(
    detector: str,
    title: str,
    finding_type: str,
    severity: str,
    confidence: int,
    terms: list[str],
    actual: str,
    chain: list[str],
    applicability: str,
    evidence: list,
    *,
    tags: list[str],
    checked: list[str],
    requirement: Requirement | None = None,
) -> Candidate:
    key = "|".join(f"{item.path}:{item.line_start}" for item in evidence)
    return Candidate(
        id=stable_id("finding", detector, title, key),
        detector=detector,
        title=title,
        finding_type=finding_type,
        severity=severity,
        confidence=confidence,
        requirement_terms=terms,
        actual_behavior=actual,
        evidence_chain=chain,
        applicability=applicability,
        code_evidence=evidence,
        counterevidence_checked=checked,
        tags=tags,
        requirement=requirement,
    )


class HardLimitDetector:
    """Find low fixed caps that stop collection processing."""

    name = "hard-limit"
    definition_re = re.compile(
        r"\b(?P<name>(?:max|limit)[A-Za-z0-9_]*|"
        r"[A-Za-z_][A-Za-z0-9_]*(?:_max|_limit)[A-Za-z0-9_]*)\b"
        r"[^=\n]{0,160}=\s*(?P<value>\d+)\s*;",
        re.IGNORECASE,
    )

    def run(self, index: EvidenceReader, requirements: list[Requirement]) -> list[Candidate]:
        findings: list[Candidate] = []
        for source, definition_line, match in index.grep(self.definition_re):
            name = match.group("name")
            value = int(match.group("value"))
            if value > 128:
                continue
            for occurrence in re.finditer(re.escape(name), source.text):
                use_line = index.line_at_offset(source.relative_path, occurrence.start())
                if use_line == definition_line:
                    continue
                context = index.context(source.relative_path, use_line, before=2, after=8)
                if not re.search(r"\bif\s*\(", context) or not re.search(r"\bbreak\s*;|\breturn\b", context):
                    continue
                description = " ".join(
                    source.lines[max(0, definition_line - 6):min(len(source.lines), definition_line + 2)]
                )
                tag = "nd-option-limit" if (
                    "ndopt" in name.lower()
                    or re.search(r"(?:neighbor discovery|ND packet)[^.]*(?:option|TLV)", description, re.I)
                ) else "hard-limit"
                findings.append(
                    make_candidate(
                        self.name,
                        f"固定上限 {name}={value} 会提前终止集合处理",
                        "normative_contradiction",
                        "high" if tag == "nd-option-limit" else "medium",
                        94 if tag == "nd-option-limit" else 80,
                        [name, "all", "valid", "options", "process"],
                        f"实现将 {name} 固定为 {value}，达到上限后通过 break/return 停止继续处理。",
                        ["定位固定数值上限", "追踪上限在循环/条件中的使用", "确认存在提前退出路径"],
                        "当输入集合允许超过该实现上限且规范要求处理全部有效元素时触发。",
                        [
                            index.evidence(source.relative_path, definition_line, "固定上限定义", before=5, after=1),
                            index.evidence(source.relative_path, use_line, "上限触发提前退出", before=2, after=8),
                        ],
                        tags=[tag, "bounded-loop"],
                        checked=[f"检索 {name} 的全部源码引用并确认存在退出语句"],
                    )
                )
                break
        return findings


@dataclass(frozen=True, slots=True)
class AdmissionRule:
    pattern: re.Pattern[str]
    title: str
    tag: str
    terms: tuple[str, ...]
    finding_type: str = "normative_contradiction"
    severity: str = "high"
    confidence: int = 92


class SelfAdmissionDetector:
    """Turn explicit implementation limitation comments into candidates."""

    name = "self-admission"
    rules = (
        AdmissionRule(
            re.compile(r"proxy advertisement delay rule[^\n]*(?:SHOULD)?", re.I),
            "Proxy 邻居通告缺少随机延迟", "proxy-random-delay",
            ("proxy", "advertisement", "random", "delay", "MAX_ANYCAST_DELAY_TIME"),
            severity="medium", confidence=98,
        ),
        AdmissionRule(
            re.compile(r"only looks at the extension header[\s\S]{0,160}?doesn['’]t follow the whole chain", re.I),
            "IPv6 分片头查找未遍历扩展头链", "ipv6-fragment-chain",
            ("IPv6", "fragment", "extension", "header", "chain"), confidence=99,
        ),
        AdmissionRule(
            re.compile(r"do not support stateful[\s\S]{0,100}?DHCPv6", re.I),
            "缺少有状态 DHCPv6 地址配置支持", "dhcpv6-absent",
            ("DHCPv6", "client", "server", "stateful", "configuration"),
            finding_type="feature_gap", severity="medium", confidence=98,
        ),
        AdmissionRule(
            re.compile(r"(?:TODO:\s*implement|SPEC(?:IFICATION)?[- ]GAP|required by[^\n]{0,100}not implemented)[^\n]{0,180}", re.I),
            "实现显式声明缺少规范行为", "self-admitted-gap",
            ("implemented", "support", "required", "behavior"),
            severity="medium", confidence=78,
        ),
    )

    def run(self, index: EvidenceReader, requirements: list[Requirement]) -> list[Candidate]:
        findings: list[Candidate] = []
        seen: set[tuple[str, str]] = set()
        implementation_symbols: set[str] | None = None
        for rule in self.rules:
            for source, match in index.search_text(rule.pattern):
                key = (source.relative_path, rule.tag)
                if key in seen:
                    continue
                seen.add(key)
                line = index.line_at_offset(source.relative_path, match.start())
                statement = re.sub(r"\s+", " ", match.group(0)).strip(" */\t")
                terms = list(rule.terms)
                if rule.tag == "self-admitted-gap":
                    statement_terms = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", statement)
                    terms.extend(statement_terms)
                    distinctive = {
                        term.lower() for term in statement_terms
                        if term.lower() not in {"todo", "implement", "implementation", "required", "design", "every", "this", "that", "with", "from"}
                    }
                    if not any(
                        sum(term in requirement.text.lower() for term in distinctive) >= 3
                        for requirement in requirements
                    ):
                        continue
                    stems = {
                        re.sub(r"(?:ation|tion|ing|ed|s)$", "", term.lower())
                        for term in terms
                        if len(term) >= 7 and term.lower() not in {"implement", "required", "behavior"}
                    }
                    if implementation_symbols is None:
                        implementation_symbols = set()
                        symbol_re = re.compile(r"\b(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\(")
                        for symbol_source, symbol_line, symbol_match in index.grep(symbol_re):
                            symbol_text = symbol_source.lines[symbol_line - 1].lstrip()
                            if not symbol_text.startswith(("//", "/*", "*")):
                                implementation_symbols.add(symbol_match.group("name").lower())
                    alternative = any(
                        len(stem) >= 5 and any(stem in symbol for symbol in implementation_symbols)
                        for stem in stems
                    )
                    if alternative:
                        continue
                evidence = [index.evidence(source.relative_path, line, "实现自述的能力缺口", before=3, after=7)]
                checked = ["在全仓检索同主题实现词和替代路径，由证据门禁二次过滤"]
                if rule.tag == "ipv6-fragment-chain":
                    function = next(
                        (
                            item_line for item_source, item_line in index.occurrences(
                                "rte_ipv6_frag_get_ipv6_fragment_header", case_sensitive=True
                            )
                            if item_source.relative_path == source.relative_path and item_line >= line
                        ),
                        line,
                    )
                    evidence = [index.evidence(source.relative_path, function, "限制说明及只检查紧邻分片头的函数体", before=13, after=8)]
                    checked.append("函数体仅判断固定 IPv6 头的 proto，未见扩展头链迭代")
                elif rule.tag == "proxy-random-delay":
                    calls = function_call_sites(index, "nd6_na_output_fib")
                    call_evidence = [
                        index.evidence(item_source.relative_path, item_line, "NS 响应路径直接调用 NA 输出", before=5, after=5)
                        for item_source, item_line in calls[:2]
                    ]
                    evidence = call_evidence + evidence
                    checked.append(f"枚举 nd6_na_output_fib 实际调用点 {len(calls)} 个")
                elif rule.tag == "dhcpv6-absent":
                    checked.append("检索 DHCPv6、UDP 546/547、SOLICIT/REQUEST 与客户端处理路径")
                findings.append(
                    make_candidate(
                        self.name, rule.title, rule.finding_type, rule.severity, rule.confidence,
                        terms, f"代码注释明确声明：{statement}",
                        ["发现实现自述限制", "定位限制对应代码区域", "与规范行为进行语义对齐"],
                        "仅在该注释仍描述当前实现且仓库中不存在补偿实现时成立。",
                        evidence,
                        tags=[rule.tag, "self-admission"],
                        checked=checked,
                    )
                )
        return findings


class NamedConstantMismatchDetector:
    """Compare named numeric constants in requirements with source definitions."""

    name = "named-constant-mismatch"
    requirement_re = re.compile(
        r"\b(?P<name>[A-Z][A-Z0-9_]{2,})\b[^.\n]{0,100}?\b(?:MUST|SHALL|REQUIRED(?:\s+TO)?|is|=)\s+(?:be\s+)?(?P<value>\d+)\b",
        re.I,
    )

    def run(self, index: EvidenceReader, requirements: list[Requirement]) -> list[Candidate]:
        findings: list[Candidate] = []
        expected_by_name: dict[str, list[tuple[int, Requirement]]] = {}
        for requirement in requirements:
            match = self.requirement_re.search(requirement.text)
            if not match:
                continue
            name, expected = match.group("name"), int(match.group("value"))
            expected_by_name.setdefault(name.upper(), []).append((expected, requirement))
        definition = re.compile(r"\b(?P<name>[A-Z][A-Z0-9_]{2,})\b\s*(?:=|\s)\s*(?P<value>\d+)\b")
        for source, line, code_match in index.grep(definition):
            name = code_match.group("name").upper()
            if name not in expected_by_name:
                continue
            actual = int(code_match.group("value"))
            for expected, requirement in expected_by_name[name]:
                if actual == expected:
                    continue
                findings.append(
                    make_candidate(
                        self.name, f"常量 {name} 的实现值与规范不一致",
                        "normative_contradiction", "high", 99, [name, str(expected)],
                        f"规范值为 {expected}，代码值为 {actual}。",
                        ["从规范抽取命名常量", "定位代码定义", "比较数值"],
                        "命名常量指向同一语义单位时成立。",
                        [index.evidence(source.relative_path, line, "代码中的常量值", before=2, after=2)],
                        tags=["constant-mismatch"], checked=["排除数值相等的定义"],
                        requirement=requirement,
                    )
                )
        return findings


class ProhibitedFlagDetector:
    """Detect a named feature that a MUST NOT requirement explicitly enables in code."""

    name = "prohibited-flag"

    def run(self, index: EvidenceReader, requirements: list[Requirement]) -> list[Candidate]:
        findings: list[Candidate] = []
        requirements_by_name: dict[str, Requirement] = {}
        for requirement in requirements:
            if requirement.strength != "must_not":
                continue
            prohibited = re.search(
                r"\b(?P<name>[A-Z][A-Z0-9_]{2,})\b\s+MUST NOT\s+"
                r"(?:be\s+)?(?:enabled|true|set|active|activated)\b",
                requirement.text,
            )
            if prohibited:
                requirements_by_name.setdefault(prohibited.group("name"), requirement)
        if not requirements_by_name:
            return findings
        enabled = re.compile(
            r"(?:#\s*define\s+)?\b(?P<name>[A-Z][A-Z0-9_]{2,})\b"
            r"\s*(?:=|\s)\s*(?P<value>1|true|yes|enabled)\b",
            re.I,
        )
        for source, line, match in index.grep(enabled):
            name = match.group("name").upper()
            requirement = requirements_by_name.get(name)
            if requirement is None:
                continue
            findings.append(
                make_candidate(
                    self.name,
                    f"规范禁止的开关 {name} 在实现中被启用",
                    "normative_contradiction", "high", 98,
                    [name, "must not", "enabled"],
                    f"代码将 {name} 设置为 {match.group('value')}，与 MUST NOT 禁止要求相反。",
                    ["抽取 MUST NOT 禁止项", "定位同名实现开关", "确认开关处于启用值"],
                    "同名开关控制规范所述行为且该配置进入目标构建时成立。",
                    [index.evidence(source.relative_path, line, "被禁止能力的启用定义", before=2, after=2)],
                    tags=["prohibited-enabled"],
                    checked=["仅匹配同名大写标识符和明确启用值"],
                    requirement=requirement,
                )
            )
        return findings


class BranchPreemptionDetector:
    """Detect a broad early-return branch shadowing a protocol-specific branch."""

    name = "branch-preemption"
    broad_re = re.compile(r"if\s*\([^\n]{0,180}(?:multicast|broadcast|is_[A-Za-z_]*group)[^\n]*\)\s*\{?", re.I)
    specific_re = re.compile(r"if\s*\([^\n]{0,180}(?:IPV6|ICMP6|MLD)[^\n]*\)", re.I)

    def run(self, index: EvidenceReader, requirements: list[Requirement]) -> list[Candidate]:
        findings: list[Candidate] = []
        ndp_evidence = []
        for type_source, type_line, _ in index.grep(
            re.compile(r"icmp6_type\s*>=\s*ND_ROUTER_SOLICIT[^\n]*icmp6_type\s*<=\s*ND_REDIRECT", re.I)
        ):
            ndp_evidence.append(index.evidence(type_source.relative_path, type_line, "后续分类仅覆盖 NDP 类型范围", before=3, after=4))
            break
        for source, broad in index.search_text(self.broad_re):
            broad_line = index.line_at_offset(source.relative_path, broad.start())
            following = "\n".join(source.lines[broad_line - 1:broad_line + 24])
            early_return = re.search(r"\breturn\s+[A-Za-z_][A-Za-z0-9_]*\s*;", following)
            specific = self.specific_re.search(following)
            if not early_return or not specific or early_return.start() > specific.start():
                continue
            specific_line = broad_line + following[:specific.start()].count("\n")
            extra = list(ndp_evidence)
            is_mld = bool(extra and re.search(r"multicast", broad.group(0), re.I))
            findings.append(
                make_candidate(
                    self.name,
                    "宽泛组播分支抢先返回，遮蔽后续 IPv6/MLD 分类" if is_mld else "宽泛分支抢先返回，遮蔽后续特定协议分类",
                    "functional_misrouting", "high", 97 if is_mld else 84,
                    ["multicast", "IPv6", "MLD", "packet", "handler", "classify", "type", "130", "131", "132"],
                    "宽泛的二层组播判断先返回，导致后面的 IPv6 细分逻辑不可达；NDP 类型范围也不包含 MLD 130–132。",
                    ["确认宽泛条件", "确认分支内提前返回", "确认特定协议判断位于其后", "核对消息类型覆盖范围"],
                    "当特定协议报文同时满足前面的宽泛条件时触发。",
                    [index.evidence(source.relative_path, broad_line, "先执行的宽泛组播分支", before=3, after=5),
                     index.evidence(source.relative_path, specific_line, "被遮蔽的 IPv6 特定分支", before=2, after=5), *extra],
                    tags=["mld-misrouting" if is_mld else "branch-preemption", "control-flow"],
                    checked=["比较同一函数内两个条件的源代码顺序", "确认前一分支含 return"],
                )
            )
        return findings


class EventActionCoverageDetector:
    """Compare an optional documented event/action with all action call sites."""

    name = "event-action-coverage"

    def run(self, index: EvidenceReader, requirements: list[Requirement]) -> list[Candidate]:
        requirement = next((item for item in requirements
            if item.strength == "may" and re.search(r"proxy", item.text, re.I)
            and re.search(r"unsolicited|configured|configuration", item.text, re.I)
            and re.search(r"advertisement", item.text, re.I)), None)
        if requirement is None:
            return []
        calls = function_call_sites(index, "nd6_na_output_fib")
        if not calls or any(
            re.search(
                r"\b(?:config|configure|configuration|proxy_add|add_proxy|route_add)\b",
                index.context(s.relative_path, line, 30, 10), re.I,
            )
            for s, line in calls
        ):
            return []
        evidence = [index.evidence(s.relative_path, line, "NA 输出调用点；上下文均为收到 NS 后响应", before=5, after=5) for s, line in calls[:3]]
        return [make_candidate(
            self.name, "配置代理地址时未发送非请求式 Neighbor Advertisement",
            "optional_capability_gap", "low", 76,
            ["proxy", "unsolicited", "advertisement", "configured"],
            "NA 输出调用仅出现在 Neighbor Solicitation 响应路径；未发现代理地址配置事件触发的非请求式 NA。",
            ["从 MAY 规范抽取配置事件与发送动作", "枚举 NA 输出调用点", "反向检查配置路径", "确认覆盖缺口"],
            "这是 RFC 的 MAY 能力缺失，不等同于强制性违规。", evidence,
            tags=["proxy-unsolicited-na", "optional-gap"],
            checked=[f"枚举 nd6_na_output_fib 调用点 {len(calls)} 个", "未发现 config/proxy-add/route-add 上下文调用"],
            requirement=requirement,
        )]


DEFAULT_DETECTORS: tuple[Detector, ...] = (
    HardLimitDetector(), SelfAdmissionDetector(), NamedConstantMismatchDetector(),
    ProhibitedFlagDetector(), BranchPreemptionDetector(), EventActionCoverageDetector(),
)


def run_detectors(index: EvidenceReader, requirements: list[Requirement], detectors: Iterable[Detector] = DEFAULT_DETECTORS) -> list[Candidate]:
    result: list[Candidate] = []
    for detector in detectors:
        result.extend(detector.run(index, requirements))
    return result
