import pytest
from models.priority import Priority
from models.task import Task
from models.pet import Pet
from models.owner import Owner
from services.scheduler import Scheduler
from services.plan_explainer import PlanExplainer
from constants.sample_tasks import SAMPLE_TASKS
from utils.validators import parse_priority


def make_scheduler(available_minutes=480, day_start=480, day_end=1320):
    owner = Owner(name="Alex", available_minutes=available_minutes)
    pet = Pet(name="Buddy", species="dog")
    return Scheduler(owner, pet, day_start_minute=day_start, day_end_minute=day_end), owner, pet


def test_full_flow_single_task():
    scheduler, owner, pet = make_scheduler()
    scheduler.add_task(Task(title="Walk", duration_minutes=30, priority=Priority.HIGH))
    scheduled, skipped = scheduler.generate_plan()
    explainer = PlanExplainer(scheduled, skipped, owner, pet)
    assert len(scheduled) == 1
    assert len(skipped) == 0
    assert "Buddy" in explainer.summarize()
    assert "Alex" in explainer.summarize()


def test_full_flow_all_fit():
    scheduler, owner, pet = make_scheduler(480)
    for title, dur, pri in [("Walk", 30, Priority.HIGH), ("Feed", 10, Priority.HIGH), ("Groom", 15, Priority.MEDIUM)]:
        scheduler.add_task(Task(title=title, duration_minutes=dur, priority=pri))
    scheduled, skipped = scheduler.generate_plan()
    assert len(scheduled) == 3
    assert len(skipped) == 0


def test_full_flow_some_skipped():
    scheduler, owner, pet = make_scheduler(30)
    scheduler.add_task(Task(title="Walk", duration_minutes=30, priority=Priority.HIGH))
    scheduler.add_task(Task(title="Groom", duration_minutes=15, priority=Priority.MEDIUM))
    scheduled, skipped = scheduler.generate_plan()
    assert len(scheduled) == 1
    assert len(skipped) == 1


def test_full_flow_all_completed():
    scheduler, owner, pet = make_scheduler()
    scheduler.add_task(Task(title="Walk", duration_minutes=30, priority=Priority.HIGH, completed=True))
    scheduled, skipped = scheduler.generate_plan()
    assert scheduled == []
    assert skipped == []


def test_explain_skipped_in_full_flow():
    scheduler, owner, pet = make_scheduler(30)
    scheduler.add_task(Task(title="Walk", duration_minutes=30, priority=Priority.HIGH))
    scheduler.add_task(Task(title="Groom", duration_minutes=15, priority=Priority.MEDIUM))
    scheduled, skipped = scheduler.generate_plan()
    explainer = PlanExplainer(scheduled, skipped, owner, pet)
    assert "Groom" in explainer.explain_skipped()


def test_priority_ordering_in_full_flow():
    scheduler, owner, pet = make_scheduler()
    scheduler.add_task(Task(title="Low",  duration_minutes=10, priority=Priority.LOW))
    scheduler.add_task(Task(title="High", duration_minutes=10, priority=Priority.HIGH))
    scheduler.add_task(Task(title="Med",  duration_minutes=10, priority=Priority.MEDIUM))
    scheduled, _ = scheduler.generate_plan()
    assert scheduled[0].task.title == "High"
    assert scheduled[1].task.title == "Med"
    assert scheduled[2].task.title == "Low"


def test_explain_task_output_nonempty():
    scheduler, owner, pet = make_scheduler()
    scheduler.add_task(Task(title="Walk", duration_minutes=30, priority=Priority.HIGH))
    scheduled, skipped = scheduler.generate_plan()
    explainer = PlanExplainer(scheduled, skipped, owner, pet)
    for st in scheduled:
        assert len(explainer.explain_task(st)) > 0


def test_total_minutes_matches_sum():
    scheduler, owner, pet = make_scheduler()
    scheduler.add_task(Task(title="Walk", duration_minutes=30, priority=Priority.HIGH))
    scheduler.add_task(Task(title="Feed", duration_minutes=10, priority=Priority.HIGH))
    scheduled, skipped = scheduler.generate_plan()
    explainer = PlanExplainer(scheduled, skipped, owner, pet)
    assert explainer.total_minutes_scheduled == 40


def test_sample_tasks_full_flow():
    owner = Owner(name="Test", available_minutes=840)
    pet = Pet(name="Pet", species="dog")
    scheduler = Scheduler(owner, pet)
    for entry in SAMPLE_TASKS:
        scheduler.add_task(Task(
            title=entry["title"],
            duration_minutes=entry["duration_minutes"],
            priority=parse_priority(entry["priority"]),
            category=entry["category"],
        ))
    scheduled, skipped = scheduler.generate_plan()
    explainer = PlanExplainer(scheduled, skipped, owner, pet)
    total_input = sum(e["duration_minutes"] for e in SAMPLE_TASKS)
    total_output = explainer.total_minutes_scheduled + sum(t.duration_minutes for t in skipped)
    assert total_output == total_input


def test_no_tasks_explainer():
    owner = Owner(name="Alex", available_minutes=480)
    pet = Pet(name="Buddy", species="dog")
    scheduler = Scheduler(owner, pet)
    scheduled, skipped = scheduler.generate_plan()
    explainer = PlanExplainer(scheduled, skipped, owner, pet)
    assert explainer.total_minutes_scheduled == 0
    assert explainer.explain_skipped() == ""


def test_time_continuity():
    scheduler, owner, pet = make_scheduler()
    scheduler.add_task(Task(title="A", duration_minutes=30, priority=Priority.HIGH))
    scheduler.add_task(Task(title="B", duration_minutes=15, priority=Priority.MEDIUM))
    scheduler.add_task(Task(title="C", duration_minutes=20, priority=Priority.LOW))
    scheduled, _ = scheduler.generate_plan()
    for i in range(len(scheduled) - 1):
        assert scheduled[i].end_time == scheduled[i + 1].start_time


def test_window_capped_at_day_end():
    scheduler, owner, pet = make_scheduler(available_minutes=840, day_start=480, day_end=540)
    scheduler.add_task(Task(title="Short", duration_minutes=45, priority=Priority.HIGH))
    scheduler.add_task(Task(title="Long",  duration_minutes=30, priority=Priority.MEDIUM))
    scheduled, skipped = scheduler.generate_plan()
    assert len(scheduled) == 1
    assert skipped[0].title == "Long"


def test_window_capped_at_owner_minutes():
    scheduler, owner, pet = make_scheduler(available_minutes=840, day_start=480, day_end=510)
    scheduler.add_task(Task(title="T1", duration_minutes=20, priority=Priority.HIGH))
    scheduler.add_task(Task(title="T2", duration_minutes=20, priority=Priority.MEDIUM))
    scheduled, skipped = scheduler.generate_plan()
    assert len(scheduled) == 1
    assert len(skipped) == 1


def test_reason_nonempty_for_all_scheduled():
    scheduler, owner, pet = make_scheduler()
    scheduler.add_task(Task(title="Walk", duration_minutes=30, priority=Priority.HIGH))
    scheduler.add_task(Task(title="Feed", duration_minutes=10, priority=Priority.MEDIUM))
    scheduled, _ = scheduler.generate_plan()
    for st in scheduled:
        assert st.reason != ""


def test_completed_tasks_not_in_skipped():
    scheduler, owner, pet = make_scheduler(30)
    scheduler.add_task(Task(title="Done",   duration_minutes=60, priority=Priority.HIGH, completed=True))
    scheduler.add_task(Task(title="Active", duration_minutes=20, priority=Priority.MEDIUM))
    scheduled, skipped = scheduler.generate_plan()
    assert "Done" not in [t.title for t in skipped]


def test_same_priority_preserves_insertion_order():
    scheduler, owner, pet = make_scheduler()
    scheduler.add_task(Task(title="First",  duration_minutes=10, priority=Priority.HIGH))
    scheduler.add_task(Task(title="Second", duration_minutes=10, priority=Priority.HIGH))
    scheduled, _ = scheduler.generate_plan()
    assert scheduled[0].task.title == "First"
    assert scheduled[1].task.title == "Second"


def test_summarize_is_string():
    scheduler, owner, pet = make_scheduler()
    scheduled, skipped = scheduler.generate_plan()
    explainer = PlanExplainer(scheduled, skipped, owner, pet)
    assert isinstance(explainer.summarize(), str)


def test_explain_skipped_is_string_when_nonempty():
    scheduler, owner, pet = make_scheduler(30)
    scheduler.add_task(Task(title="Walk",  duration_minutes=30, priority=Priority.HIGH))
    scheduler.add_task(Task(title="Extra", duration_minutes=30, priority=Priority.MEDIUM))
    scheduled, skipped = scheduler.generate_plan()
    explainer = PlanExplainer(scheduled, skipped, owner, pet)
    assert isinstance(explainer.explain_skipped(), str)
