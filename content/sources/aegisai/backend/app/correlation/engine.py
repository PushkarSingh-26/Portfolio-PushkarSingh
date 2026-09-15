"""Correlation engine: apply the rule base to CVE text, score, and persist.

Scoring methodology (deterministic + explainable)
-------------------------------------------------
1. For each CVE description, every rule whose phrases appear (as whole words)
   contributes its weight to the technique it maps to.
2. When several rules point at the same technique, their weights combine with a
   noisy-OR: ``score = 1 - Π(1 - wᵢ)``. Independent signals reinforce each
   other and the result stays in [0, 1].
3. The score is bucketed: HIGH ≥ 0.7, MEDIUM ≥ 0.4, otherwise LOW.
4. The matched phrases are stored verbatim as the evidence for the link, so
   every correlation is auditable.

Everything here is pure and deterministic - the same inputs always yield the
same correlations, which is what makes the engine testable and explainable.
"""

import re
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.correlation.rules import RULES, CorrelationRule

METHOD = "rule-based-keyword-v1"

HIGH_THRESHOLD = 0.7
MEDIUM_THRESHOLD = 0.4


def _compile(pattern: str) -> re.Pattern:
    """Compile a phrase with alphanumeric-edge boundaries.

    Avoids false hits like 'dos' inside 'windows' while still allowing
    non-word phrases such as '../'. An optional trailing 's' is permitted so a
    singular phrase ('arbitrary command') also matches its plural in CVE text
    ('arbitrary commands') without matching unrelated words ('commander').
    """
    body = re.escape(pattern)
    prefix = r"(?<![A-Za-z0-9])" if pattern[0].isalnum() else ""
    suffix = r"s?(?![A-Za-z0-9])" if pattern[-1].isalnum() else ""
    return re.compile(prefix + body + suffix, re.IGNORECASE)


# Precompile once at import time: [(rule, [(phrase, regex), ...]), ...]
_COMPILED: list[tuple[CorrelationRule, list[tuple[str, re.Pattern]]]] = [
    (rule, [(p, _compile(p)) for p in rule.patterns]) for rule in RULES
]


def combine_weights(weights: Iterable[float]) -> float:
    """Noisy-OR combination of independent rule weights."""
    product = 1.0
    for w in weights:
        product *= (1.0 - w)
    return round(1.0 - product, 3)


def confidence_level(score: float) -> str:
    if score >= HIGH_THRESHOLD:
        return "HIGH"
    if score >= MEDIUM_THRESHOLD:
        return "MEDIUM"
    return "LOW"


def find_matches(description: str | None) -> dict[str, dict]:
    """Return {technique_id: {weights, keywords, tactic}} for one CVE text."""
    if not description:
        return {}

    result: dict[str, dict] = {}
    for rule, compiled in _COMPILED:
        hits = [phrase for phrase, rx in compiled if rx.search(description)]
        if not hits:
            continue
        entry = result.setdefault(
            rule.technique_id,
            {"weights": [], "keywords": set(), "tactic": None, "_best": -1.0},
        )
        entry["weights"].append(rule.weight)
        entry["keywords"].update(hits)
        # Keep the tactic from the strongest rule for this technique.
        if rule.weight > entry["_best"]:
            entry["_best"] = rule.weight
            entry["tactic"] = rule.tactic
    return result


def correlate_description(description: str | None) -> list[dict]:
    """Public, DB-free helper: scored correlations for a single description."""
    matches = find_matches(description)
    out = []
    for technique_id, info in matches.items():
        score = combine_weights(info["weights"])
        out.append(
            {
                "technique_id": technique_id,
                "tactic": info["tactic"],
                "confidence_score": score,
                "confidence_level": confidence_level(score),
                "matched_keywords": sorted(info["keywords"]),
            }
        )
    return sorted(out, key=lambda d: d["confidence_score"], reverse=True)


def run_correlation(
    db: Session, valid_technique_ids: set[str] | None = None
) -> dict:
    """Correlate every stored CVE against the rule base and upsert results."""
    # Local imports to avoid a circular import at module load.
    from backend.app.models import CVE, CorrelationResult, Technique

    if valid_technique_ids is None:
        valid_technique_ids = {
            row[0] for row in db.execute(select(Technique.technique_id)).all()
        }

    existing = {
        (c.technique_id, c.cve_id): c
        for c in db.query(CorrelationResult).all()
    }

    cves = db.execute(select(CVE.cve_id, CVE.description)).all()

    inserted = updated = unchanged = 0
    cves_with_matches = 0

    for cve_id, description in cves:
        matches = find_matches(description)
        produced = False
        for technique_id, info in matches.items():
            if technique_id not in valid_technique_ids:
                continue
            produced = True
            score = combine_weights(info["weights"])
            level = confidence_level(score)
            keywords = ", ".join(sorted(info["keywords"]))
            key = (technique_id, cve_id)

            current = existing.get(key)
            if current is None:
                db.add(
                    CorrelationResult(
                        technique_id=technique_id,
                        cve_id=cve_id,
                        confidence_score=score,
                        confidence_level=level,
                        tactic=info["tactic"],
                        method=METHOD,
                        matched_keywords=keywords,
                    )
                )
                inserted += 1
            elif (
                current.confidence_score != score
                or current.matched_keywords != keywords
                or current.tactic != info["tactic"]
            ):
                current.confidence_score = score
                current.confidence_level = level
                current.tactic = info["tactic"]
                current.matched_keywords = keywords
                current.method = METHOD
                updated += 1
            else:
                unchanged += 1
        if produced:
            cves_with_matches += 1

    db.commit()
    return {
        "cves_analyzed": len(cves),
        "cves_with_matches": cves_with_matches,
        "inserted": inserted,
        "updated": updated,
        "unchanged": unchanged,
        "total_correlations": inserted + updated + unchanged,
    }


def main() -> int:
    from backend.app.database import SessionLocal

    print("Running rule-based ATT&CK <-> CVE correlation ...")
    with SessionLocal() as db:
        stats = run_correlation(db)
    print(
        f"Done. Analyzed {stats['cves_analyzed']} CVEs; "
        f"{stats['cves_with_matches']} produced matches.\n"
        f"Correlations - inserted: {stats['inserted']}, "
        f"updated: {stats['updated']}, unchanged: {stats['unchanged']}, "
        f"total: {stats['total_correlations']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
