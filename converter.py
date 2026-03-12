import re

GREEKLISH_MULTI: dict = {
    "ps": "ψ",
    "ou": "ου",
    "ai": "αι",
    "ei": "ει",
    "oi": "οι",
    "au": "αυ",
    "eu": "ευ",
    "mp": "μπ",
    "nt": "ντ",
    "gk": "γκ",
    "gg": "γγ",
}

GREEKLISH_SINGLE: dict = {
    "a": "α",
    "b": "β",
    "v": "β",
    "g": "γ",
    "d": "δ",
    "e": "ε",
    "z": "ζ",
    "h": "η",
    "8": "θ",
    "i": "ι",
    "k": "κ",
    "l": "λ",
    "m": "μ",
    "n": "ν",
    "3": "ξ",
    "o": "ο",
    "p": "π",
    "r": "ρ",
    "s": "σ",
    "t": "τ",
    "u": "υ",
    "y": "υ",
    "f": "φ",
    "x": "χ",
    "w": "ω",
    "?": ";",
}

# Pre-compiled regexes
_RE_BACKTICK = re.compile(r"`([^`]*)`")
_RE_SIGMA_WORD = re.compile(r"\bσ\b")
_RE_SIGMA_BOUNDARY = re.compile(r"σ([,.!?;:)\]»\s]|$)")

# Cached compiled greeklish substitution regex (rebuilt only when the profile changes)
_greeklish_regex: re.Pattern | None = None
_greeklish_regex_keys: tuple = ()


def _build_greeklish_regex() -> re.Pattern:
    # Placeholder pattern must come first so it is never transliterated
    placeholder = r"\x00PASSTHROUGH\d+\x00"
    # Multi-char patterns before single chars so longer matches take priority
    keys = sorted((str(k) for k in GREEKLISH_MULTI), key=len, reverse=True) + [str(k) for k in GREEKLISH_SINGLE]
    return re.compile(placeholder + "|" + "|".join(re.escape(str(k)) for k in keys), re.IGNORECASE)


def _preserve_case(source: str, target: str) -> str:
    if source.isupper():
        return target.upper()
    if source[:1].isupper():
        return target[:1].upper() + target[1:]
    return target


def greeklish_to_greek(text: str) -> str:
    """Convert Greeklish text to Greek. Wrap words in backticks to pass them through unchanged."""
    global _greeklish_regex, _greeklish_regex_keys

    passthroughs: list[str] = []

    def _stash(m: re.Match) -> str:
        passthroughs.append(m.group(1))
        return f"\x00PASSTHROUGH{len(passthroughs) - 1}\x00"

    escaped = _RE_BACKTICK.sub(_stash, text)

    current_keys = (tuple(GREEKLISH_MULTI), tuple(GREEKLISH_SINGLE))
    if _greeklish_regex is None or _greeklish_regex_keys != current_keys:
        _greeklish_regex = _build_greeklish_regex()
        _greeklish_regex_keys = current_keys

    def _replace_match(m: re.Match) -> str:
        chunk = m.group(0)
        if chunk[0] == "\x00":
            return passthroughs[int(chunk[len("\x00PASSTHROUGH"):-1])]
        lower = chunk.lower()
        if lower in GREEKLISH_MULTI:
            return _preserve_case(chunk, GREEKLISH_MULTI[lower])
        return _preserve_case(chunk, GREEKLISH_SINGLE[lower])

    return second_pass_corrections(_greeklish_regex.sub(_replace_match, escaped))


def second_pass_corrections(text: str) -> str:
    """Fix final sigma and double semicolons."""
    corrected = _RE_SIGMA_WORD.sub("ς", text)
    corrected = _RE_SIGMA_BOUNDARY.sub(r"ς\1", corrected)
    return corrected.replace(";;", ";")
