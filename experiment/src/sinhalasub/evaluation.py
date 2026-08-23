"""Validation and confidential aggregation of blinded evaluator responses."""

import math
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .experiment_package import (
    CRITICAL_ERROR_CATEGORIES,
    KEY_SCHEMA,
    PACKAGE_SCHEMA,
    RUBRIC_DIMENSIONS,
    package_digest,
)


RESPONSE_SCHEMA = "sinhalasub.evaluator-response.v1"
ANALYSIS_SCHEMA = "sinhalasub.evaluation-analysis.v1"
def aggregate_evaluator_responses(
    package: Mapping[str, Any],
    key: Mapping[str, Any],
    responses: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    _validate_package_and_key(package, key)
    if not responses:
        raise ValueError("At least one evaluator response is required.")

    evaluator_ids = [str(response.get("evaluator_id", "")).strip() for response in responses]
    if any(not evaluator_id for evaluator_id in evaluator_ids) or len(set(evaluator_ids)) != len(evaluator_ids):
        raise ValueError("Evaluator IDs must be present and unique.")

    package_blocks = {block["id"]: block for block in package["blocks"]}
    key_blocks = {block["block_id"]: block for block in key["blocks"]}
    system_ids = [system["id"] for system in key["systems"]]
    values = {
        system_id: {
            "scores": {dimension: [] for dimension in RUBRIC_DIMENSIONS},
            "preferences": 0,
            "critical_errors": [],
            "critical_error_categories": {category: 0 for category in CRITICAL_ERROR_CATEGORIES},
        }
        for system_id in system_ids
    }
    preference_by_block = {
        block_id: {system_id: 0 for system_id in system_ids}
        for block_id in package_blocks
    }
    strata: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for response in responses:
        _validate_response(response, package, package_blocks)
        for block_response in response["blocks"]:
            block_id = block_response["block_id"]
            key_block = key_blocks[block_id]
            label_map = key_block["labels"]
            stratum_keys = [("genre", str(key_block.get("genre", "unspecified")))] + [
                ("challenge", str(tag)) for tag in key_block.get("challenge_tags", [])
            ]
            for candidate in block_response["candidates"]:
                system_id = label_map[candidate["label"]]
                category_counts = _critical_error_counts(candidate)
                for dimension in RUBRIC_DIMENSIONS:
                    values[system_id]["scores"][dimension].append(int(candidate["scores"][dimension]))
                values[system_id]["critical_errors"].append(int(candidate["critical_errors"]))
                for category, count in category_counts.items():
                    values[system_id]["critical_error_categories"][category] += count
                if candidate["preferred"]:
                    values[system_id]["preferences"] += 1
                    preference_by_block[block_id][system_id] += 1
                for stratum_key in stratum_keys:
                    stratum = strata.setdefault(stratum_key, _empty_stratum(system_ids))
                    system_stratum = stratum[system_id]
                    system_stratum["observations"] += 1
                    system_stratum["preferences"] += int(candidate["preferred"])
                    system_stratum["critical_errors"] += int(candidate["critical_errors"])
                    for category, count in category_counts.items():
                        system_stratum["critical_error_categories"][category] += count

    observations = len(responses) * len(package_blocks)
    systems = []
    for system_id in system_ids:
        system = values[system_id]
        rubric_means = {
            dimension: round(_mean(system["scores"][dimension]), 4)
            for dimension in RUBRIC_DIMENSIONS
        }
        preference_count = int(system["preferences"])
        systems.append(
            {
                "system_id": system_id,
                "observations": observations,
                "rubric_means": rubric_means,
                "overall_rubric_mean": round(_mean(tuple(rubric_means.values())), 4),
                "preference_count": preference_count,
                "preference_rate": round(preference_count / observations, 4),
                "preference_ci_95": [round(bound, 4) for bound in _wilson_interval(preference_count, observations)],
                "critical_error_total": sum(system["critical_errors"]),
                "critical_errors_per_block": round(_mean(system["critical_errors"]), 4),
                "critical_error_categories": dict(system["critical_error_categories"]),
            }
        )

    return {
        "schema_version": ANALYSIS_SCHEMA,
        "experiment_id": package["experiment_id"],
        "package_sha256": package_digest(package),
        "evaluator_count": len(responses),
        "block_count": len(package_blocks),
        "preference_fleiss_kappa": _fleiss_kappa(tuple(preference_by_block.values()), len(responses)),
        "systems": systems,
        "strata": [
            {
                "kind": kind,
                "value": value,
                "systems": [
                    {
                        "system_id": system_id,
                        "observations": system["observations"],
                        "preference_count": system["preferences"],
                        "preference_rate": round(system["preferences"] / system["observations"], 4),
                        "critical_error_total": system["critical_errors"],
                        "critical_error_categories": dict(system["critical_error_categories"]),
                    }
                    for system_id, system in stratum.items()
                ],
            }
            for (kind, value), stratum in sorted(strata.items())
        ],
    }


def _validate_package_and_key(package: Mapping[str, Any], key: Mapping[str, Any]) -> None:
    if package.get("schema_version") != PACKAGE_SCHEMA or key.get("schema_version") != KEY_SCHEMA:
        raise ValueError("Unsupported package or key schema.")
    if package.get("experiment_id") != key.get("experiment_id"):
        raise ValueError("Package and key experiment IDs do not match.")
    if package_digest(package) != key.get("package_sha256"):
        raise ValueError("Package hash does not match the confidential key.")
    package_block_ids = [block["id"] for block in package["blocks"]]
    key_block_ids = [block["block_id"] for block in key["blocks"]]
    if package_block_ids != key_block_ids:
        raise ValueError("Package and key blocks do not match.")
    system_ids = {system["id"] for system in key["systems"]}
    for package_block, key_block in zip(package["blocks"], key["blocks"]):
        package_labels = {candidate["label"] for candidate in package_block["candidates"]}
        if set(key_block["labels"]) != package_labels or set(key_block["labels"].values()) != system_ids:
            raise ValueError("Confidential key candidate mappings do not match the package and systems.")
        genre = key_block.get("genre")
        tags = key_block.get("challenge_tags")
        if not isinstance(genre, str) or not genre.strip():
            raise ValueError("Confidential key blocks require a genre.")
        if not isinstance(tags, list) or len(tags) != len(set(tags)) or any(not isinstance(tag, str) or not tag for tag in tags):
            raise ValueError("Confidential key block challenge tags must be unique non-empty strings.")


def _validate_response(
    response: Mapping[str, Any],
    package: Mapping[str, Any],
    package_blocks: Mapping[str, Mapping[str, Any]],
) -> None:
    if response.get("schema_version") != RESPONSE_SCHEMA:
        raise ValueError("Unsupported evaluator response schema.")
    if response.get("experiment_id") != package.get("experiment_id"):
        raise ValueError("Evaluator response experiment ID does not match package.")
    if response.get("package_sha256") != package_digest(package):
        raise ValueError("Evaluator response package hash does not match package.")

    response_blocks = response.get("blocks", [])
    if [block.get("block_id") for block in response_blocks] != list(package_blocks):
        raise ValueError("Evaluator response must include every block exactly once in package order.")
    for block_response in response_blocks:
        block = package_blocks[block_response["block_id"]]
        expected_labels = [candidate["label"] for candidate in block["candidates"]]
        candidates = block_response.get("candidates", [])
        if [candidate.get("label") for candidate in candidates] != expected_labels:
            raise ValueError("Evaluator response must include every candidate exactly once in package order.")
        if sum(candidate.get("preferred") is True for candidate in candidates) != 1:
            raise ValueError("Each block must have exactly one preferred candidate.")
        for candidate in candidates:
            scores = candidate.get("scores", {})
            if set(scores) != set(RUBRIC_DIMENSIONS):
                raise ValueError("Every candidate must include all rubric dimensions and no unknown dimensions.")
            if any(type(score) is not int or score < 1 or score > 5 for score in scores.values()):
                raise ValueError("Rubric scores must be integers from 1 to 5.")
            critical_errors = candidate.get("critical_errors")
            if type(critical_errors) is not int or critical_errors < 0:
                raise ValueError("Critical errors must be a non-negative integer.")
            categories = candidate.get("critical_error_categories")
            if categories is not None:
                if not isinstance(categories, dict) or not set(categories) <= set(CRITICAL_ERROR_CATEGORIES) - {"unclassified"}:
                    raise ValueError("Critical-error categories contain unsupported values.")
                if any(type(count) is not int or count < 0 for count in categories.values()):
                    raise ValueError("Critical-error category counts must be non-negative integers.")
                if sum(categories.values()) != critical_errors:
                    raise ValueError("Critical-error category counts must equal critical_errors.")
            if type(candidate.get("preferred")) is not bool:
                raise ValueError("Preferred must be a boolean.")


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _critical_error_counts(candidate: Mapping[str, Any]) -> Dict[str, int]:
    categories = candidate.get("critical_error_categories")
    if categories is None:
        return {"unclassified": int(candidate["critical_errors"])}
    return {str(category): int(count) for category, count in categories.items()}


def _empty_stratum(system_ids: Sequence[str]) -> Dict[str, Any]:
    return {
        system_id: {
            "observations": 0,
            "preferences": 0,
            "critical_errors": 0,
            "critical_error_categories": {category: 0 for category in CRITICAL_ERROR_CATEGORIES},
        }
        for system_id in system_ids
    }


def _wilson_interval(successes: int, observations: int, z: float = 1.96) -> Tuple[float, float]:
    proportion = successes / observations
    denominator = 1 + z * z / observations
    center = (proportion + z * z / (2 * observations)) / denominator
    margin = z * math.sqrt(
        proportion * (1 - proportion) / observations + z * z / (4 * observations * observations)
    ) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def _fleiss_kappa(block_counts: Sequence[Mapping[str, int]], raters: int) -> Any:
    if raters < 2 or not block_counts:
        return None
    categories = tuple(block_counts[0])
    observed = _mean(
        [
            (sum(counts[category] ** 2 for category in categories) - raters) / (raters * (raters - 1))
            for counts in block_counts
        ]
    )
    total_ratings = len(block_counts) * raters
    category_proportions = {
        category: sum(counts[category] for counts in block_counts) / total_ratings
        for category in categories
    }
    expected = sum(proportion ** 2 for proportion in category_proportions.values())
    if expected == 1:
        return 1.0 if observed == 1 else None
    return round((observed - expected) / (1 - expected), 4)
