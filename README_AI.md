# PawPal+ — Developer Reference

**Project:** Pet care daily scheduler with AI-powered task recommendations  
**Stack:** Python 3.10+, Streamlit, Google Gemini 2.5 Flash, Pytest  
**Entry point:** `app.py` → `streamlit run app.py`  
**AI model:** `gemini-2.5-flash` via `google-genai` SDK

---

## Architecture

```
app.py  (UI / orchestration)
  ├── models/         pure data, no logic
  ├── services/       business logic
  │   ├── scheduler.py
  │   ├── plan_explainer.py
  │   └── ai_recommender.py
  ├── utils/          validation, parsing, prompt-injection guard
  └── constants/      breed lists, sample tasks, 100-task CSV database
```

Data flows one direction: `app.py` builds model objects from validated user input → optionally calls `PetAIRecommender` to fetch AI task suggestions → passes tasks to `Scheduler` → passes results to `PlanExplainer` → renders markdown output.

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
Integer value is used directly as the sort key (higher = scheduled first). Do not change these values without updating `Scheduler` sort logic.

### `Pet` — `models/pet.py`
```python
@dataclass
class Pet:
    name: str
    species: str    # validated: dog|cat|rabbit|bird|other
    breed: str = ""
    age: int = 0
    notes: str = ""
```

### `Owner` — `models/owner.py`
```python
@dataclass
class Owner:
    name: str
    available_minutes: int = 480    # validated: 30–840
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
Produced only by `Scheduler.generate_plan()`. Never constructed directly in `app.py`.

---

## Services (`services/`)

### `Scheduler` — `services/scheduler.py`

```python
class Scheduler:
    def __init__(self, owner: Owner, pet: Pet,
                 day_start_minute: int = 480,    # 08:00
                 day_end_minute: int = 1320)      # 22:00

    def add_task(task: Task) -> None
    def remove_task(title: str) -> None           # safe no-op if not found
    def generate_plan() -> tuple[list[ScheduledTask], list[Task]]
```

**`generate_plan()` algorithm** (greedy, priority-first):
1. Filter out `task.completed == True`
2. Sort remaining by `task.priority.value` descending (HIGH first)
3. Available window = `min(owner.available_minutes, day_end_minute - day_start_minute)`
4. Walk tasks in sorted order; place each if it fits in remaining minutes
5. Tasks that don't fit → `skipped_tasks` list
6. Return `(scheduled_tasks, skipped_tasks)`

Time slots are absolute minutes from midnight; `_minutes_to_time(int) -> "HH:MM"` converts for display.

---

### `PlanExplainer` — `services/plan_explainer.py`

```python
class PlanExplainer:
    def __init__(self, scheduled_tasks: list[ScheduledTask],
                 skipped_tasks: list[Task], owner: Owner, pet: Pet)

    def summarize() -> str                          # markdown summary line
    def explain_task(st: ScheduledTask) -> str      # per-task markdown line
    def explain_skipped() -> str                    # markdown block for skipped tasks
```

Output is markdown strings for direct rendering in Streamlit. `total_minutes_scheduled` (int) is computed in `__init__` as the sum of all scheduled task durations. Priority indicators: 🔴 HIGH, 🟡 MEDIUM, 🟢 LOW.

---

### `PetAIRecommender` — `services/ai_recommender.py`

```python
class PetAIRecommender:
    def __init__(self, api_key: str, csv_path: Optional[Path] = None)

    def get_recommendations(
        pet: Pet,
        pet_notes: str,
        max_context_tasks: int = 15,
        max_recommendations: int = 7,
    ) -> RecommendationResult
```

**Return types:**
```python
@dataclass
class TaskRecommendation:
    title: str
    category: str
    duration_minutes: int
    priority: str           # "high" | "medium" | "low"
    reason: str             # 2-3 sentence pet-specific explanation
    basis: str              # "breed_data" | "owner_notes" | "both"

@dataclass
class RecommendationResult:
    recommendations: list[TaskRecommendation]
    summary: str
    error: Optional[str] = None
```

**Recommendation pipeline:**

1. Load `constants/tasks.csv` (100 tasks, each with breed-compatibility data)
2. Extract keywords from `pet_notes` (3+ letter words, stop words filtered via `_STOP_WORDS`)
3. Score every task: `base_score = Priority value for breed` + `0.4 per keyword match` in title/category
4. Pass top `max_context_tasks` (default 15) scored tasks + full pet profile to Gemini
5. Gemini responds with JSON: 3–`max_recommendations` selected tasks, per-task reasoning, and a summary
6. Validate response: discard any titles not present in the provided task list
7. Return `RecommendationResult`

**Gemini call:**
```python
self._client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.3,
    ),
)
```

**Error handling:** All exceptions from the API call are caught and returned as `RecommendationResult(error=str(exc))`. The UI surfaces these without crashing.

---

## Utils (`utils/validators.py`)

```python
VALID_SPECIES = {"dog", "cat", "rabbit", "bird", "other"}
PRIORITY_MAP  = {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}

validate_duration(minutes: int) -> int           # raises ValueError if < 1
validate_available_minutes(minutes: int) -> int  # raises ValueError if outside 30–840
validate_species(species: str) -> str            # strips, lowercases, validates
parse_priority(priority_str: str) -> Priority    # case-insensitive string → enum
validate_pet_notes(notes: str) -> str            # sanitises and rejects prompt injection
```

`validate_pet_notes` enforces a 1000-character cap and rejects notes containing patterns such as `ignore instructions`, `jailbreak`, `<<SYS>>`, and similar prompt-injection markers. Called in `app.py` before notes are passed to `PetAIRecommender`.

All validators raise `ValueError` with descriptive messages on bad input.

---

## Constants (`constants/`)

### `breed_options.py`
```python
BREED_OPTIONS: dict[str, list[str]]
# Keys: "dog", "cat", "rabbit", "bird", "other"
# Values: sorted lists of breed name strings for UI selectbox
```

### `sample_tasks.py`
```python
SAMPLE_TASKS: list[dict]
# 10 dicts, each with keys: title, duration_minutes, priority, category
# Maps directly to Task(**entry)
```

### `tasks.csv`
100 pet care tasks used by `PetAIRecommender`. Schema:

| Column           | Description                                                             |
|------------------|-------------------------------------------------------------------------|
| `title`          | Task name (exact string matched against AI response)                    |
| `duration_minutes` | Integer                                                               |
| `category`       | exercise \| feeding \| grooming \| enrichment \| health \| training \| hygiene |
| `viable_breeds`  | Encoded breed→priority pairs: `("Labrador Retriever",high)("Poodle",medium)` |

The `viable_breeds` field is parsed by `_parse_viable_breeds()` using regex `_BREED_PATTERN`. Falls back to `"Mixed / Other"` if the pet's breed is not found.

---

## App (`app.py`)

Streamlit page with five sections:

1. **Owner & Pet** — name inputs, hours/minutes available, pet name/species/breed/age
2. **AI Task Recommendations** — enabled when `GEMINI_API_KEY` is set and pet notes are provided; calls `PetAIRecommender.get_recommendations()`; results cached in `st.session_state["ai_recs"]`
3. **Add Care Tasks** — form adds tasks to `st.session_state["tasks"]`; "Load sample tasks" button; per-task delete buttons; "Clear all"
4. **Generate Schedule** — triggers validation, model construction, and scheduling:
   ```python
   scheduler = Scheduler(owner, pet)
   for task in tasks:
       scheduler.add_task(task)
   scheduled, skipped = scheduler.generate_plan()
   explainer = PlanExplainer(scheduled, skipped, owner, pet)
   # render summarize(), explain_task(), explain_skipped()
   ```
5. **Session state keys:**
   - `st.session_state["tasks"]` — list of raw task dicts before `Task` construction
   - `st.session_state["ai_recs"]` — cached `RecommendationResult`
   - `st.session_state["ai_error"]` — cached error string from last AI call

---

## Tests (`tests/`)

| File                     | Coverage focus                                            | ~Cases |
|--------------------------|-----------------------------------------------------------|--------|
| `test_models.py`         | Priority ordering, Task/Pet/Owner/breed construction      | 24     |
| `test_scheduler.py`      | add/remove, priority sort, time window, skipping          | 15     |
| `test_plan_explainer.py` | summarize, explain_task, explain_skipped, edge cases      | 14     |
| `test_validators.py`     | All validators including validate_pet_notes, edge cases   | 15     |
| `test_constants.py`      | SAMPLE_TASKS structure, breed_options coverage            | 7      |
| `test_integration.py`    | Full Scheduler→PlanExplainer flows, AI recommender mocks  | 19     |

Run: `pytest tests/`

---

## Key Invariants

- `Scheduler.generate_plan()` never mutates input tasks — completed tasks are excluded by filter, not mutation
- `remove_task()` is a no-op if the title doesn't match — no exception raised
- `PlanExplainer` is stateless after `__init__`; all methods are pure given constructor arguments
- `Priority.value` (1/2/3) is used directly for sorting — changing enum integers breaks the scheduler
- Available window is capped at `min(owner.available_minutes, day_end_minute - day_start_minute)`
- `PetAIRecommender` only returns tasks whose titles appear in the list it sent to the model — the AI cannot inject arbitrary tasks into the schedule
- Pet notes pass through `validate_pet_notes()` before reaching the AI — prompt injection is blocked at the app layer, not inside the recommender
