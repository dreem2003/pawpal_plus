import pytest
from models.priority import Priority
from models.task import Task
from models.pet import Pet
from models.owner import Owner
from services.scheduler import Scheduler


@pytest.fixture
def owner():
    return Owner(name="Alex", available_minutes=480)


@pytest.fixture
def pet():
    return Pet(name="Buddy", species="dog")


@pytest.fixture
def scheduler(owner, pet):
    return Scheduler(owner, pet)


@pytest.fixture
def high_task():
    return Task(title="Walk", duration_minutes=30, priority=Priority.HIGH)


@pytest.fixture
def medium_task():
    return Task(title="Groom", duration_minutes=15, priority=Priority.MEDIUM)


@pytest.fixture
def low_task():
    return Task(title="Cuddle", duration_minutes=20, priority=Priority.LOW)


def test_add_task(scheduler, high_task):
    scheduler.add_task(high_task)
    assert len(scheduler._tasks) == 1


def test_add_multiple_tasks(scheduler, high_task, medium_task, low_task):
    scheduler.add_task(high_task)
    scheduler.add_task(medium_task)
    scheduler.add_task(low_task)
    assert len(scheduler._tasks) == 3


def test_remove_task(scheduler, high_task):
    scheduler.add_task(high_task)
    scheduler.remove_task("Walk")
    assert len(scheduler._tasks) == 0


def test_remove_task_noop_if_not_found(scheduler, high_task):
    scheduler.add_task(high_task)
    scheduler.remove_task("Nonexistent")
    assert len(scheduler._tasks) == 1


def test_remove_task_by_title(scheduler, high_task, medium_task):
    scheduler.add_task(high_task)
    scheduler.add_task(medium_task)
    scheduler.remove_task("Walk")
    assert scheduler._tasks == [medium_task]


def test_generate_plan_returns_tuple(scheduler, high_task):
    scheduler.add_task(high_task)
    result = scheduler.generate_plan()
    assert isinstance(result, tuple) and len(result) == 2


def test_generate_plan_priority_order(scheduler, low_task, high_task, medium_task):
    scheduler.add_task(low_task)
    scheduler.add_task(high_task)
    scheduler.add_task(medium_task)
    scheduled, _ = scheduler.generate_plan()
    assert scheduled[0].task.priority == Priority.HIGH
    assert scheduled[1].task.priority == Priority.MEDIUM
    assert scheduled[2].task.priority == Priority.LOW


def test_generate_plan_excludes_completed(scheduler):
    done = Task(title="Done", duration_minutes=10, priority=Priority.HIGH, completed=True)
    active = Task(title="Active", duration_minutes=10, priority=Priority.MEDIUM)
    scheduler.add_task(done)
    scheduler.add_task(active)
    scheduled, skipped = scheduler.generate_plan()
    titles = [s.task.title for s in scheduled]
    assert "Done" not in titles
    assert "Active" in titles


def test_generate_plan_start_at_0800(scheduler, high_task):
    scheduler.add_task(high_task)
    scheduled, _ = scheduler.generate_plan()
    assert scheduled[0].start_time == "08:00"
    assert scheduled[0].end_time == "08:30"


def test_generate_plan_sequential_times(scheduler, high_task, medium_task):
    scheduler.add_task(high_task)
    scheduler.add_task(medium_task)
    scheduled, _ = scheduler.generate_plan()
    assert scheduled[0].end_time == scheduled[1].start_time


def test_generate_plan_skips_when_no_room():
    owner = Owner(name="Alex", available_minutes=30)
    pet = Pet(name="Buddy", species="dog")
    s = Scheduler(owner, pet)
    s.add_task(Task(title="Walk", duration_minutes=30, priority=Priority.HIGH))
    s.add_task(Task(title="Groom", duration_minutes=15, priority=Priority.MEDIUM))
    scheduled, skipped = s.generate_plan()
    assert len(scheduled) == 1
    assert len(skipped) == 1
    assert skipped[0].title == "Groom"


def test_generate_plan_respects_available_minutes():
    owner = Owner(name="Alex", available_minutes=45)
    pet = Pet(name="Buddy", species="dog")
    s = Scheduler(owner, pet)
    s.add_task(Task(title="Long", duration_minutes=60, priority=Priority.HIGH))
    scheduled, skipped = s.generate_plan()
    assert len(scheduled) == 0
    assert len(skipped) == 1


def test_generate_plan_empty(scheduler):
    scheduled, skipped = scheduler.generate_plan()
    assert scheduled == []
    assert skipped == []


def test_generate_plan_does_not_mutate_tasks(scheduler, high_task):
    scheduler.add_task(high_task)
    scheduler.generate_plan()
    assert high_task.completed is False


def test_minutes_to_time(scheduler):
    assert scheduler._minutes_to_time(480) == "08:00"
    assert scheduler._minutes_to_time(0) == "00:00"
    assert scheduler._minutes_to_time(1320) == "22:00"
    assert scheduler._minutes_to_time(545) == "09:05"
