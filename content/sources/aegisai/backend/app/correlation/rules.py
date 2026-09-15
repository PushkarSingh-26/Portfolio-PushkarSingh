"""Rule base for ATT&CK <-> CVE correlation.

Each rule maps a set of high-signal exploitation-vector phrases to a single
ATT&CK technique, its tactic, and a base weight (how strongly the phrase
implies the technique). The rules are intentionally conservative - we favor
precision over recall, so a correlation is only emitted when a recognized
exploitation vector appears in the CVE description.

Weights are the per-rule probability that the match is meaningful. When more
than one rule fires for the same technique on the same CVE, the engine combines
their weights with a noisy-OR (see engine.combine_weights), so independent
signals reinforce each other without ever exceeding 1.0.

This rule base is versioned in code (not the database) so it is reviewable in
git and can be replaced by an ML/graph model in a later phase without touching
the schema.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CorrelationRule:
    technique_id: str          # MITRE ATT&CK technique referenced
    tactic: str                # ATT&CK tactic the vector maps to
    weight: float              # base confidence contribution (0.0-1.0)
    patterns: tuple[str, ...]  # phrases matched as whole words (case-insensitive)
    label: str                 # human-readable description of the rule


# Ordered roughly by ATT&CK tactic. technique_id values are validated against
# the ingested ATT&CK data at runtime; unknown techniques are skipped.
RULES: tuple[CorrelationRule, ...] = (
    # ── Initial Access ──────────────────────────────────────
    CorrelationRule(
        "T1190", "Initial Access", 0.7,
        ("sql injection", "sqli", "deserialization", "xml external entity",
         "xxe", "server-side request forgery", "ssrf", "local file inclusion",
         "remote file inclusion", "lfi", "rfi"),
        "Exploitation of a public-facing application weakness",
    ),
    CorrelationRule(
        "T1133", "Initial Access", 0.5,
        ("vpn", "remote desktop", "rdp", "external remote service"),
        "Abuse of external remote services",
    ),
    CorrelationRule(
        "T1566", "Initial Access", 0.8,
        ("phishing", "spear-phishing", "spearphishing", "spear phishing"),
        "Phishing delivery vector",
    ),

    # ── Execution ───────────────────────────────────────────
    CorrelationRule(
        "T1059", "Execution", 0.7,
        ("command injection", "os command injection", "arbitrary command",
         "command execution", "code injection", "shell command"),
        "Command and scripting interpreter abuse",
    ),
    CorrelationRule(
        "T1059.007", "Execution", 0.6,
        ("cross-site scripting", "cross site scripting", "xss"),
        "JavaScript execution via cross-site scripting",
    ),
    CorrelationRule(
        "T1203", "Execution", 0.5,
        ("buffer overflow", "stack overflow", "heap overflow",
         "out-of-bounds write", "out of bounds write", "use-after-free",
         "use after free", "type confusion", "integer overflow",
         "arbitrary code execution", "execute arbitrary code",
         "remote code execution", "rce"),
        "Memory-safety/exploitation primitive enabling code execution",
    ),

    # ── Persistence ─────────────────────────────────────────
    CorrelationRule(
        "T1505.003", "Persistence", 0.8,
        ("web shell", "webshell"),
        "Web shell persistence",
    ),

    # ── Privilege Escalation ────────────────────────────────
    CorrelationRule(
        "T1068", "Privilege Escalation", 0.7,
        ("privilege escalation", "elevate privilege", "elevation of privilege",
         "gain privileges", "gain elevated", "escalate privileges"),
        "Exploitation for privilege escalation",
    ),

    # ── Defense Evasion / Valid Accounts ────────────────────
    CorrelationRule(
        "T1078", "Defense Evasion", 0.5,
        ("authentication bypass", "bypass authentication", "auth bypass",
         "improper authentication", "missing authentication"),
        "Authentication bypass enabling use of valid accounts",
    ),

    # ── Credential Access ───────────────────────────────────
    CorrelationRule(
        "T1110", "Credential Access", 0.7,
        ("brute force", "brute-force"),
        "Brute-force credential attack",
    ),
    CorrelationRule(
        "T1552", "Credential Access", 0.6,
        ("hardcoded password", "hard-coded password", "hardcoded credential",
         "hard-coded credential", "default credential", "cleartext password",
         "plaintext password"),
        "Unsecured credentials exposed",
    ),
    CorrelationRule(
        "T1003", "Credential Access", 0.6,
        ("credential dumping", "dump credentials", "lsass"),
        "OS credential dumping",
    ),
    CorrelationRule(
        "T1539", "Credential Access", 0.5,
        ("session fixation", "session hijack", "steal session", "session token"),
        "Theft of web session cookie/token",
    ),

    # ── Discovery ───────────────────────────────────────────
    CorrelationRule(
        "T1083", "Discovery", 0.4,
        ("directory traversal", "path traversal", "../", "arbitrary file read"),
        "Path traversal enabling file/directory discovery",
    ),

    # ── Lateral Movement / Hijack ───────────────────────────
    CorrelationRule(
        "T1574", "Persistence", 0.7,
        ("dll hijack", "dll side-loading", "dll sideloading",
         "dll preloading", "dll search order"),
        "Hijack execution flow via DLL",
    ),

    # ── Collection ──────────────────────────────────────────
    CorrelationRule(
        "T1056.001", "Collection", 0.7,
        ("keylogger", "keylogging", "keystroke logging"),
        "Keylogging input capture",
    ),

    # ── Credential Access / Network ─────────────────────────
    CorrelationRule(
        "T1557", "Credential Access", 0.7,
        ("man-in-the-middle", "man in the middle", "mitm", "on-path attack"),
        "Adversary-in-the-middle interception",
    ),

    # ── Impact ──────────────────────────────────────────────
    CorrelationRule(
        "T1486", "Impact", 0.8,
        ("ransomware", "data encrypted for impact", "file encryption malware"),
        "Data encrypted for impact (ransomware)",
    ),
    CorrelationRule(
        "T1499", "Impact", 0.6,
        ("denial of service", "denial-of-service", "dos vulnerability",
         "reachable assertion", "infinite loop", "resource exhaustion"),
        "Endpoint denial of service",
    ),
)
