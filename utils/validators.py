from models.priority import Priority

VALID_SPECIES = {"dog", "cat", "rabbit", "bird", "other"}
PRIORITY_MAP = {
    "low": Priority.LOW,
    "medium": Priority.MEDIUM,
    "high": Priority.HIGH,
}


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
