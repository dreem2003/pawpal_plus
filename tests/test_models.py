import pytest
from models.priority import Priority
from models.task import Task, ScheduledTask
from models.pet import Pet
from models.owner import Owner


# ── Priority ──────────────────────────────────────────────────────────────────

def test_priority_values():
    assert Priority.LOW.value == 1
    assert Priority.MEDIUM.value == 2
    assert Priority.HIGH.value == 3


def test_priority_ordering():
    assert Priority.HIGH.value > Priority.MEDIUM.value
    assert Priority.MEDIUM.value > Priority.LOW.value


def test_priority_sort_descending():
    priorities = [Priority.LOW, Priority.HIGH, Priority.MEDIUM]
    result = sorted(priorities, key=lambda p: p.value, reverse=True)
    assert result == [Priority.HIGH, Priority.MEDIUM, Priority.LOW]


def test_priority_names():
    assert Priority.LOW.name == "LOW"
    assert Priority.MEDIUM.name == "MEDIUM"
    assert Priority.HIGH.name == "HIGH"


# ── Task ──────────────────────────────────────────────────────────────────────

def test_task_defaults():
    task = Task(title="Walk", duration_minutes=30, priority=Priority.HIGH)
    assert task.category == "general"
    assert task.completed is False


def test_task_fields():
    task = Task(title="Feed", duration_minutes=10, priority=Priority.MEDIUM, category="feeding")
    assert task.title == "Feed"
    assert task.duration_minutes == 10
    assert task.priority == Priority.MEDIUM
    assert task.category == "feeding"


def test_task_mark_complete():
    task = Task(title="Walk", duration_minutes=30, priority=Priority.HIGH)
    task.mark_complete()
    assert task.completed is True


def test_task_mark_complete_idempotent():
    task = Task(title="Walk", duration_minutes=30, priority=Priority.HIGH)
    task.mark_complete()
    task.mark_complete()
    assert task.completed is True


def test_task_completed_flag_default_false():
    task = Task(title="Walk", duration_minutes=30, priority=Priority.LOW)
    assert task.completed is False


# ── ScheduledTask ─────────────────────────────────────────────────────────────

def test_scheduled_task_defaults():
    task = Task(title="Walk", duration_minutes=30, priority=Priority.HIGH)
    st = ScheduledTask(task=task, start_time="08:00", end_time="08:30")
    assert st.reason == ""


def test_scheduled_task_fields():
    task = Task(title="Walk", duration_minutes=30, priority=Priority.HIGH)
    st = ScheduledTask(task=task, start_time="08:00", end_time="08:30", reason="First task")
    assert st.task is task
    assert st.start_time == "08:00"
    assert st.end_time == "08:30"
    assert st.reason == "First task"


# ── Pet ───────────────────────────────────────────────────────────────────────

def test_pet_defaults():
    pet = Pet(name="Buddy", species="dog")
    assert pet.age == 0
    assert pet.notes == ""


def test_pet_fields():
    pet = Pet(name="Whiskers", species="cat", age=5, notes="indoor")
    assert pet.name == "Whiskers"
    assert pet.species == "cat"
    assert pet.age == 5
    assert pet.notes == "indoor"


# ── Owner ─────────────────────────────────────────────────────────────────────

def test_owner_defaults():
    owner = Owner(name="Alex")
    assert owner.available_minutes == 480
    assert owner.preferences == ""
    assert owner.pets == []


def test_owner_add_pet():
    owner = Owner(name="Alex")
    pet = Pet(name="Buddy", species="dog")
    owner.add_pet(pet)
    assert len(owner.pets) == 1
    assert owner.pets[0] is pet


def test_owner_add_multiple_pets():
    owner = Owner(name="Alex")
    owner.add_pet(Pet(name="Buddy", species="dog"))
    owner.add_pet(Pet(name="Whiskers", species="cat"))
    assert len(owner.pets) == 2


def test_owner_pets_list_independent():
    owner1 = Owner(name="Alex")
    owner2 = Owner(name="Sam")
    owner1.add_pet(Pet(name="Buddy", species="dog"))
    assert len(owner2.pets) == 0


def test_owner_custom_minutes():
    owner = Owner(name="Sam", available_minutes=120)
    assert owner.available_minutes == 120
