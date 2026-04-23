import pytest
from models.priority import Priority
from models.task import Task, ScheduledTask
from models.pet import Pet
from models.owner import Owner
from services.plan_explainer import PlanExplainer


@pytest.fixture
def owner():
    return Owner(name="Alex", available_minutes=480)


@pytest.fixture
def pet():
    return Pet(name="Buddy", species="dog")


def make_scheduled(title, duration, priority, start, end, reason="", category="general"):
    task = Task(title=title, duration_minutes=duration, priority=priority, category=category)
    return ScheduledTask(task=task, start_time=start, end_time=end, reason=reason)


def make_skipped(title, duration, priority):
    return Task(title=title, duration_minutes=duration, priority=priority)


def test_total_minutes_scheduled(owner, pet):
    st1 = make_scheduled("Walk", 30, Priority.HIGH, "08:00", "08:30")
    st2 = make_scheduled("Feed", 10, Priority.HIGH, "08:30", "08:40")
    explainer = PlanExplainer([st1, st2], [], owner, pet)
    assert explainer.total_minutes_scheduled == 40


def test_total_minutes_scheduled_empty(owner, pet):
    explainer = PlanExplainer([], [], owner, pet)
    assert explainer.total_minutes_scheduled == 0


def test_summarize_contains_pet_name(owner, pet):
    explainer = PlanExplainer([], [], owner, pet)
    assert "Buddy" in explainer.summarize()


def test_summarize_contains_owner_name(owner, pet):
    explainer = PlanExplainer([], [], owner, pet)
    assert "Alex" in explainer.summarize()


def test_summarize_shows_scheduled_count(owner, pet):
    st = make_scheduled("Walk", 30, Priority.HIGH, "08:00", "08:30")
    explainer = PlanExplainer([st], [], owner, pet)
    assert "1" in explainer.summarize()


def test_summarize_shows_skipped_count(owner, pet):
    skipped = make_skipped("Groom", 15, Priority.MEDIUM)
    explainer = PlanExplainer([], [skipped], owner, pet)
    assert "1" in explainer.summarize()


def test_summarize_is_string(owner, pet):
    explainer = PlanExplainer([], [], owner, pet)
    assert isinstance(explainer.summarize(), str)


def test_explain_task_contains_title(owner, pet):
    st = make_scheduled("Walk", 30, Priority.HIGH, "08:00", "08:30", reason="High priority")
    explainer = PlanExplainer([st], [], owner, pet)
    assert "Walk" in explainer.explain_task(st)


def test_explain_task_contains_times(owner, pet):
    st = make_scheduled("Walk", 30, Priority.HIGH, "08:00", "08:30", reason="High priority")
    explainer = PlanExplainer([st], [], owner, pet)
    output = explainer.explain_task(st)
    assert "08:00" in output
    assert "08:30" in output


def test_explain_task_contains_reason(owner, pet):
    st = make_scheduled("Walk", 30, Priority.HIGH, "08:00", "08:30", reason="First task of the day")
    explainer = PlanExplainer([st], [], owner, pet)
    assert "First task of the day" in explainer.explain_task(st)


def test_explain_task_contains_category(owner, pet):
    st = make_scheduled("Walk", 30, Priority.HIGH, "08:00", "08:30",
                        reason="High priority", category="exercise")
    explainer = PlanExplainer([st], [], owner, pet)
    assert "exercise" in explainer.explain_task(st)


def test_explain_skipped_empty_string(owner, pet):
    explainer = PlanExplainer([], [], owner, pet)
    assert explainer.explain_skipped() == ""


def test_explain_skipped_contains_title(owner, pet):
    skipped = make_skipped("Groom", 15, Priority.MEDIUM)
    explainer = PlanExplainer([], [skipped], owner, pet)
    assert "Groom" in explainer.explain_skipped()


def test_explain_skipped_multiple(owner, pet):
    s1 = make_skipped("Groom", 15, Priority.MEDIUM)
    s2 = make_skipped("Play", 20, Priority.LOW)
    explainer = PlanExplainer([], [s1, s2], owner, pet)
    output = explainer.explain_skipped()
    assert "Groom" in output
    assert "Play" in output


def test_explain_skipped_is_string(owner, pet):
    skipped = make_skipped("Groom", 15, Priority.MEDIUM)
    explainer = PlanExplainer([], [skipped], owner, pet)
    assert isinstance(explainer.explain_skipped(), str)
