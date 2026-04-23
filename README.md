# PawPal+

A Streamlit web app that helps pet owners plan and schedule daily pet care tasks. Given an owner's available time and a list of tasks, PawPal+ generates a prioritized daily schedule with time slots and plain-language explanations.

---

## What It Does

- Owner enters their name and how many minutes they have available each day
- Owner enters their pet's name, species, and age
- Owner adds care tasks (title, duration, priority, category)
- App generates an optimized schedule: high-priority tasks are slotted first, tasks that don't fit are flagged as skipped
- Each scheduled task shows a start/end time and a reason it was placed where it was

---

## Project Structure

```
pawpal_plus/
├── app.py                  # Streamlit UI entry point
├── requirements.txt        # Dependencies
├── models/                 # Data classes
│   ├── priority.py         # Priority enum (LOW, MEDIUM, HIGH)
│   ├── task.py             # Task and ScheduledTask dataclasses
│   ├── pet.py              # Pet dataclass
│   └── owner.py            # Owner dataclass
├── services/               # Business logic
│   ├── scheduler.py        # Generates the daily plan
│   └── plan_explainer.py   # Formats plan output as markdown
├── utils/
│   └── validators.py       # Input validation and priority string parsing
|── assets/
│   └──                     # system architecture screenshots, images.
├── constants/
│   └── sample_tasks.py     # 10 pre-built sample pet care tasks
└── tests/                  # Pytest test suite (40+ tests)
```

---

## Setup

**Requirements**: Python 3.10+

1. Clone or download the project folder.

2. (Recommended) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Mac/Linux
   venv\Scripts\activate         # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the app:
   ```bash
   streamlit run app.py
   ```
   The app opens in your browser at `http://localhost:8501`.

---

## Running Tests

```bash
pytest tests/
```

All 40+ tests should pass. Tests cover models, scheduler logic, plan explainer output, validators, constants, and end-to-end integration.

---

## How the Schedule Is Generated

1. Tasks are filtered to exclude already-completed ones.
2. Remaining tasks are sorted by priority: `HIGH → MEDIUM → LOW`.
3. Tasks are placed sequentially starting at 08:00, each beginning where the previous one ends.
4. The scheduling window is capped at the smaller of: the owner's available minutes, or the span from 08:00 to 22:00.
5. Any task that doesn't fit in the remaining window is skipped (not rescheduled).

---

## Sample Tasks

Ten built-in tasks are available in `constants/sample_tasks.py` for quick testing:

| Task                   | Duration | Priority | Category    |
|------------------------|----------|----------|-------------|
| Morning walk           | 30 min   | HIGH     | exercise    |
| Breakfast feeding      | 10 min   | HIGH     | feeding     |
| Evening walk           | 30 min   | HIGH     | exercise    |
| Dinner feeding         | 10 min   | HIGH     | feeding     |
| Vet medication         | 5 min    | HIGH     | health      |
| Brushing/grooming      | 15 min   | MEDIUM   | grooming    |
| Playtime               | 20 min   | MEDIUM   | enrichment  |
| Training session       | 15 min   | MEDIUM   | training    |
| Litter box cleanup     | 10 min   | LOW      | hygiene     |
| Socialisation/cuddles  | 20 min   | LOW      | enrichment  |

---

## Valid Input Ranges

| Field              | Valid Values                            |
|--------------------|-----------------------------------------|
| Available minutes  | 30 – 840 (30 min to 14 hours)           |
| Task duration      | 1+ minutes                              |
| Species            | dog, cat, rabbit, bird, other           |
| Priority           | low, medium, high (case-insensitive)    |
