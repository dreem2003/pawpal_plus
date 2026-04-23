import pytest
from models.priority import Priority
from utils.validators import (
    PRIORITY_MAP,
    VALID_SPECIES,
    parse_priority,
    validate_available_minutes,
    validate_duration,
    validate_species,
)


# ── validate_duration ─────────────────────────────────────────────────────────

def test_validate_duration_minimum():
    assert validate_duration(1) == 1


def test_validate_duration_valid():
    assert validate_duration(30) == 30
    assert validate_duration(480) == 480


def test_validate_duration_zero_raises():
    with pytest.raises(ValueError):
        validate_duration(0)


def test_validate_duration_negative_raises():
    with pytest.raises(ValueError):
        validate_duration(-10)


# ── validate_available_minutes ────────────────────────────────────────────────

def test_validate_available_minutes_lower_boundary():
    assert validate_available_minutes(30) == 30


def test_validate_available_minutes_upper_boundary():
    assert validate_available_minutes(840) == 840


def test_validate_available_minutes_mid():
    assert validate_available_minutes(480) == 480


def test_validate_available_minutes_below_min_raises():
    with pytest.raises(ValueError):
        validate_available_minutes(29)


def test_validate_available_minutes_above_max_raises():
    with pytest.raises(ValueError):
        validate_available_minutes(841)


def test_validate_available_minutes_zero_raises():
    with pytest.raises(ValueError):
        validate_available_minutes(0)


# ── validate_species ──────────────────────────────────────────────────────────

def test_validate_species_all_valid():
    for s in ["dog", "cat", "rabbit", "bird", "other"]:
        assert validate_species(s) == s


def test_validate_species_uppercase():
    assert validate_species("DOG") == "dog"
    assert validate_species("Cat") == "cat"


def test_validate_species_strips_whitespace():
    assert validate_species("  dog  ") == "dog"


def test_validate_species_invalid_raises():
    with pytest.raises(ValueError):
        validate_species("fish")


def test_validate_species_empty_raises():
    with pytest.raises(ValueError):
        validate_species("")


# ── parse_priority ────────────────────────────────────────────────────────────

def test_parse_priority_low():
    assert parse_priority("low") == Priority.LOW


def test_parse_priority_medium():
    assert parse_priority("medium") == Priority.MEDIUM


def test_parse_priority_high():
    assert parse_priority("high") == Priority.HIGH


def test_parse_priority_case_insensitive():
    assert parse_priority("HIGH") == Priority.HIGH
    assert parse_priority("Medium") == Priority.MEDIUM
    assert parse_priority("LOW") == Priority.LOW


def test_parse_priority_strips_whitespace():
    assert parse_priority("  high  ") == Priority.HIGH


def test_parse_priority_invalid_raises():
    with pytest.raises(ValueError):
        parse_priority("urgent")


def test_parse_priority_empty_raises():
    with pytest.raises(ValueError):
        parse_priority("")


# ── Constants ─────────────────────────────────────────────────────────────────

def test_valid_species_contains_expected():
    assert {"dog", "cat", "rabbit", "bird", "other"} == VALID_SPECIES


def test_priority_map_keys():
    assert set(PRIORITY_MAP.keys()) == {"low", "medium", "high"}
