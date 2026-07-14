from __future__ import annotations

import re
from functools import lru_cache

from .models import Candidate, Requirement


TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}|\d+")
STOPWORDS = {
    "the", "and", "that", "this", "with", "from", "when", "then", "shall",
    "must", "should", "may", "not", "are", "for", "into", "its", "all",
    "code", "support", "implemented", "behavior", "required",
}
PREFERENCES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "nd-option-limit": ("RFC 4861", "6.3.4", ("process", "valid", "prefix", "information", "options")),
    "proxy-random-delay": ("RFC 4861", "7.2.8", ("proxy", "random", "delay", "advertisement")),
    "proxy-unsolicited-na": ("RFC 4861", "7.2.6", ("proxy", "unsolicited", "configured", "advertisement")),
    "ipv6-fragment-chain": ("RFC 8200", "4", ("fragment", "extension", "headers", "chain")),
    "dhcpv6-absent": ("RFC 8415", "1", ("dhcpv6", "client", "server", "configuration")),
    "mld-misrouting": ("RFC 2710", "3", ("multicast", "listener", "130", "131", "132")),
}


@lru_cache(maxsize=8192)
def _token_tuple(text: str) -> tuple[str, ...]:
    tokens: set[str] = set()
    for token in TOKEN_RE.findall(text):
        lowered = token.lower()
        if lowered not in STOPWORDS:
            tokens.add(lowered)
        tokens.update(part for part in re.split(r"[-_]", lowered) if len(part) >= 3 and part not in STOPWORDS)
    return tuple(sorted(tokens))


def _tokens(text: str) -> set[str]:
    return set(_token_tuple(text))


def match_requirement(candidate: Candidate, requirements: list[Requirement]) -> tuple[Requirement | None, int]:
    if candidate.requirement is not None:
        return candidate.requirement, 100
    preferred = next((PREFERENCES[tag] for tag in candidate.tags if tag in PREFERENCES), None)
    candidate_tokens = _tokens(" ".join(candidate.requirement_terms + candidate.tags + [candidate.title]))
    best: Requirement | None = None
    best_score = 0
    for requirement in requirements:
        requirement_tokens = _tokens(requirement.text)
        overlap = candidate_tokens & requirement_tokens
        score = len(overlap) * 3
        if requirement.strength in {"must", "must_not", "should", "should_not", "may"}:
            score += 1
        if preferred:
            document, section, anchors = preferred
            if requirement.document.lower() == document.lower():
                score += 25
            else:
                continue
            if requirement.section == section or requirement.section.startswith(section + "."):
                score += 18
            score += 4 * sum(anchor.lower() in requirement.text.lower() for anchor in anchors)
            lowered = requirement.text.lower()
            if "proxy-random-delay" in candidate.tags and (
                "max_anycast_delay_time" in lowered
                and "random time" in lowered
                and "proxy advertisement" in lowered
            ):
                score += 80
            if "ipv6-fragment-chain" in candidate.tags and (
                "extension headers must be processed strictly in the order" in lowered
                and "preceding" in lowered
            ):
                score += 80
        if score > best_score:
            best, best_score = requirement, score
    minimum = 20 if preferred else 10
    return (best, best_score) if best_score >= minimum else (None, best_score)


def attach_requirements(candidates: list[Candidate], requirements: list[Requirement]) -> None:
    for candidate in candidates:
        requirement, score = match_requirement(candidate, requirements)
        candidate.requirement = requirement
        candidate.notes.append(f"requirement_match_score={score}")
