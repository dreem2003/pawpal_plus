# PawPal+ — AI Reference

**Project**: Pet care daily scheduler  
**Stack**: Python 3.10+, Streamlit, Pytest  
**Entry point**: `app.py` → `streamlit run app.py`  
**Source root**: `ai110-module2show-pawpal-starter/`

---

## Architecture

```
app.py  (UI / orchestration)
  └── models/        (pure data, no logic)
  └── services/      (business logic)
  └── utils/         (validation, parsing)
  └── constants/     (static seed data)
  └── tests/         (pytest, 40+ cases)
```

Data flows one direction: `app.py` creates model objects from user input → passes them to `Scheduler` → passes results to `PlanExplainer` → displays markdown output.

---

## Models (`models/`)

All are dataclasses or enums. No business logic lives here.

### `Priority` — `models/priority.py`
```python
class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
```
Integer value is used directly as the sort key (higher = scheduled first).

### `Pet` — `models/pet.py`
```python
@dataclass
class Pet:
    name: str
    species: str          # validated: dog|cat|rabbit|bird|other
    age: int = 0
    notes: str = ""
```

### `Owner` — `models/owner.py`
```python
@dataclass
class Owner:
    name: str
    available_minutes: int = 480   # validated: 30–840
    preferences: str = ""
    pets: list[Pet] = field(default_factory=list)

    def add_pet(pet: Pet) -> None
```

### `Task` — `models/task.py`
```python
@dataclass
class Task:
    title: str
    duration_minutes: int    # validated: >= 1
    priority: Priority
    category: str = "general"
    completed: bool = False

    def mark_complete() -> None
```

### `ScheduledTask` — `models/task.py`
```python
@dataclass
class ScheduledTask:
    task: Task
    start_time: str    # "HH:MM"
    end_time: str      # "HH:MM"
    reason: str = ""
```
Produced only by `Scheduler.generate_plan()`. Not constructed directly in `app.py`.

---

## Services (`services/`)

### `Scheduler` — `services/scheduler.py`

```python
class Scheduler:
    def __init__(self, owner: Owner, pet: Pet,
                 day_start_minute: int = 480,   # 08:00
                 day_end_minute: int = 1320)     # 22:00

    def add_task(task: Task) -> None
    def remove_task(title: str) -> None          # safe if not found
    def generate_plan() -> tuple[list[ScheduledTask], list[Task]]
```

**`generate_plan()` algorithm** (greedy, priority-first):
1. Filter out `task.completed == True`
2. Sort remaining by `task.priority.value` descending (HIGH first)
3. Available window = `min(owner.available_minutes, day_end_minute - day_start_minute)`
4. Walk tasks in sorted order; place each if it fits in remaining minutes
5. Tasks that don't fit → `skipped_tasks` list
6. Returns `(scheduled_tasks, skipped_tasks)`

Time slots: absolute minutes from midnight. `_minutes_to_time(int) -> "HH:MM"` converts for display.

### `PlanExplainer` — `services/plan_explainer.py`

```python
class PlanExplainer:
    def __init__(self, scheduled_tasks: list[ScheduledTask],
                 skipped_tasks: list[Task], owner: Owner, pet: Pet)

    def summarize() -> str          # markdown summary line
    def explain_task(st: ScheduledTask) -> str   # per-task markdown line
    def explain_skipped() -> str    # markdown block for skipped tasks
```

Output is markdown strings intended for direct rendering in Streamlit. `total_minutes_scheduled` (int) is computed in `__init__` as the sum of all scheduled task durations.

---

## Utils (`utils/validators.py`)

```python
VALID_SPECIES = {"dog", "cat", "rabbit", "bird", "other"}
PRIORITY_MAP  = {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}

validate_duration(minutes: int) -> int          # raises ValueError if < 1
validate_available_minutes(minutes: int) -> int # raises ValueError if outside 30–840
validate_species(species: str) -> str           # strips, lowercases, validates
parse_priority(priority_str: str) -> Priority   # case-insensitive string → enum
```

All validators raise `ValueError` with descriptive messages on bad input. Called in `app.py` before constructing model objects.

---

## Constants (`constants/sample_tasks.py`)

```python
SAMPLE_TASKS: list[dict]   # 10 dicts, each with keys: title, duration_minutes, priority, category
```

Each dict maps directly to `Task(**entry)`. Used in tests and optionally surfaced in the UI.

---

## App (`app.py`)

Streamlit page. Three sections:

1. **Owner & Pet** — text inputs + number input + selectbox → `Owner`, `Pet` objects
2. **Task input** — form adds tasks to `st.session_state["tasks"]` (list of dicts); "Clear all" resets it
3. **Generate schedule** — button triggers:
   ```python
   scheduler = Scheduler(owner, pet)
   for task in tasks: scheduler.add_task(task)
   scheduled, skipped = scheduler.generate_plan()
   explainer = PlanExplainer(scheduled, skipped, owner, pet)
   # render explainer.summarize(), explainer.explain_task(), explainer.explain_skipped()
   ```

Session state key: `st.session_state["tasks"]` — list of raw dicts before `Task` construction.

---

## Tests (`tests/`)

| File                    | Coverage focus                                      | ~Cases |
|-------------------------|-----------------------------------------------------|--------|
| `test_models.py`        | Priority ordering, Task/Pet/Owner construction      | 24     |
| `test_scheduler.py`     | add/remove, priority sort, time window, skipping    | 15     |
| `test_plan_explainer.py`| summarize, explain_task, explain_skipped, edge cases| 14     |
| `test_validators.py`    | All four validators, edge and error cases           | 15     |
| `test_constants.py`     | SAMPLE_TASKS structure and Task instantiation       | 7      |
| `test_integration.py`   | Full Scheduler→PlanExplainer flows, edge cases      | 19     |

Run: `pytest tests/`

---

## Key Invariants

- `Scheduler.generate_plan()` never mutates input tasks — `completed` tasks are excluded by filter, not by mutation
- `remove_task()` is a no-op if the title doesn't match — no exception raised
- `PlanExplainer` is stateless after `__init__`; all methods are pure given the constructor arguments
- `Priority.value` (1/2/3) is used directly for sorting — do not change enum integer values without updating scheduler sort logic
- Available window is capped at `min(owner.available_minutes, day_end_minute - day_start_minute)` — owner time takes precedence when it's shorter than the day span
