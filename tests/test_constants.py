import pytest
from constants.sample_tasks import SAMPLE_TASKS
from models.task import Task
from utils.validators import parse_priority, validate_duration


def test_sample_tasks_is_list():
    assert isinstance(SAMPLE_TASKS, list)


def test_sample_tasks_count():
    assert len(SAMPLE_TASKS) == 10


def test_sample_tasks_have_required_keys():
    required = {"title", "duration_minutes", "priority", "category"}
    for entry in SAMPLE_TASKS:
        assert required.issubset(entry.keys()), f"Missing keys in: {entry}"


def test_sample_tasks_titles_nonempty_strings():
    for entry in SAMPLE_TASKS:
        assert isinstance(entry["title"], str)
        assert len(entry["title"]) > 0


def test_sample_tasks_durations_valid():
    for entry in SAMPLE_TASKS:
        assert isinstance(entry["duration_minutes"], int)
        validate_duration(entry["duration_minutes"])


def test_sample_tasks_priorities_valid():
    for entry in SAMPLE_TASKS:
        parse_priority(entry["priority"])


def test_sample_tasks_can_instantiate_task():
    for entry in SAMPLE_TASKS:
        task = Task(
            title=entry["title"],
            duration_minutes=entry["duration_minutes"],
            priority=parse_priority(entry["priority"]),
            category=entry["category"],
        )
        assert task.title == entry["title"]
        assert task.completed is False
