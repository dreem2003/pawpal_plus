import re
from typing import List, Tuple

from models.priority import Priority

VALID_SPECIES = {"dog", "cat", "rabbit", "bird", "other"}
PRIORITY_MAP = {
    "low": Priority.LOW,
    "medium": Priority.MEDIUM,
    "high": Priority.HIGH,
}

_MAX_NOTES_LENGTH = 1000
_MIN_USEFUL_LENGTH = 10

# Patterns that suggest prompt-injection attempts in free-text fields
_INJECTION_PATTERNS = [
    (r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", "contains instruction-override text"),
    (r"you\s+are\s+now\s+(a|an)\s+\w+", "attempts to redefine the AI role"),
    (r"<<SYS>>|\[INST\]|\[/INST\]", "contains model control tokens"),
    (r"jailbreak|DAN\s*mode", "contains adversarial keywords"),
    (r"disregard\s+(your|all|the)\s+\w+", "attempts to override AI behaviour"),
    (r"forget\s+(your|all)\s+(previous|prior|training)", "attempts to reset AI context"),
    (r"(system|assistant|user)\s*:\s*\[", "contains role-injection markers"),
]


def validate_duration(minutes: int) -> int:
    if minutes < 1:
        raise ValueError(f"Task duration must be at least 1 minute, got {minutes}.")
    return minutes


def validate_available_minutes(minutes: int) -> int:
    if minutes < 30 or minutes > 840:
        raise ValueError(
            f"Available minutes must be between 30 and 840, got {minutes}."
        )
    return minutes


def validate_species(species: str) -> str:
    species = species.strip().lower()
    if species not in VALID_SPECIES:
        raise ValueError(
            f"Species must be one of {sorted(VALID_SPECIES)}, got '{species}'."
        )
    return species


def parse_priority(priority_str: str) -> Priority:
    key = priority_str.strip().lower()
    if key not in PRIORITY_MAP:
        raise ValueError(
            f"Priority must be one of {list(PRIORITY_MAP.keys())}, got '{priority_str}'."
        )
    return PRIORITY_MAP[key]


def validate_pet_notes(notes: str) -> Tuple[str, List[str]]:
    """Sanitise and validate pet notes before passing to the AI.

    Returns (sanitised_notes, warnings).
    Raises ValueError for content that exceeds limits or contains injection attempts.
    """
    sanitised = " ".join(notes.split())

    if len(sanitised) > _MAX_NOTES_LENGTH:
        raise ValueError(
            f"Pet notes must not exceed {_MAX_NOTES_LENGTH} characters "
            f"(got {len(sanitised)})."
        )

    warnings: List[str] = []
    if sanitised and len(sanitised) < _MIN_USEFUL_LENGTH:
        warnings.append(
            "Notes are very short — more detail helps the AI make better recommendations."
        )

    for pattern, description in _INJECTION_PATTERNS:
        if re.search(pattern, sanitised, re.IGNORECASE):
            raise ValueError(
                f"Pet notes contain invalid content ({description}). "
                "Please describe your pet's activities, health, or preferences instead."
            )

    return sanitised, warnings
