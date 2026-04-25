# PawPal+

A Streamlit web app that helps pet owners plan and schedule daily pet care tasks. Enter your available time, describe your pet, and PawPal+ generates a prioritised daily schedule — optionally powered by a Gemini AI assistant that recommends breed-specific care tasks based on your pet's individual needs.

---

## What It Does

- Owner enters their name and daily available time (30 min – 14 hours)
- Owner enters their pet's name, species, breed, and age
- **AI Recommendations (optional):** If a Gemini API key is configured and pet notes are provided, the AI analyses your pet's profile and recommends 3–7 personalised care tasks drawn from a database of 100 breed-indexed tasks, each with a specific explanation of why it suits your pet
- Owner can add AI-recommended tasks to their schedule with one click, or add tasks manually, or load 10 built-in sample tasks
- App generates an optimised schedule: HIGH-priority tasks are slotted first (from 08:00), followed by MEDIUM then LOW; tasks that don't fit the available window are flagged as skipped
- Each scheduled task shows a start/end time and a plain-language reason it was placed there

---

## Project Structure

```
pawpal_plus/
├── app.py                        # Streamlit UI entry point
├── requirements.txt              # Python dependencies
├── .env                          # Local secrets (GEMINI_API_KEY) — not committed
├── models/                       # Pure data structures, no business logic
│   ├── priority.py               # Priority enum (LOW=1, MEDIUM=2, HIGH=3)
│   ├── task.py                   # Task and ScheduledTask dataclasses
│   ├── pet.py                    # Pet dataclass
│   └── owner.py                  # Owner dataclass
├── services/                     # Business logic
│   ├── scheduler.py              # Greedy priority-first scheduling algorithm
│   ├── plan_explainer.py         # Formats schedule output as markdown
│   └── ai_recommender.py         # Gemini AI integration for task recommendations
├── utils/
│   └── validators.py             # Input validation, priority parsing, prompt-injection guard
├── constants/
│   ├── breed_options.py          # Breed lists per species (for UI selectbox)
│   ├── sample_tasks.py           # 10 pre-built sample tasks for quick testing
│   └── tasks.csv                 # 100 pet care tasks with breed-compatibility data
├── assets/                       # Architecture screenshots and images
└── tests/                        # Pytest suite (40+ tests)
```

---

## Setup

**Requirements:** Python 3.10+

### 1. Clone or download the project

```bash
git clone <repo-url>
cd pawpal_plus
```

### 2. Create and activate a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate      # Mac / Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_api_key_here
```

To get a free Gemini API key, visit [Google AI Studio](https://aistudio.google.com) and create a key. The app runs without this key — AI recommendations will simply be unavailable.

### 5. Run the app

```bash
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`.

---

## Running Tests

```bash
pytest tests/
```

All 40+ tests should pass. The suite covers models, scheduler logic, plan explainer output, validators, constants, and end-to-end integration. The AI recommender tests run without a live API key using mocked responses.

---

## How the Schedule Is Generated

1. Tasks marked as completed are filtered out.
2. Remaining tasks are sorted by priority: `HIGH → MEDIUM → LOW`.
3. Tasks are placed sequentially from 08:00, each starting where the previous ends.
4. The available window is capped at the smaller of: the owner's available minutes, or the 08:00–22:00 day span.
5. Any task that does not fit in the remaining window is skipped (listed separately, not rescheduled).

---

## AI Recommendations

When a `GEMINI_API_KEY` is present and pet notes are provided:

1. The app extracts keywords from the owner's notes and scores all 100 tasks in `constants/tasks.csv` against the pet's breed and those keywords.
2. The top 15 matching tasks are passed to Gemini 2.5 Flash along with the full pet profile and owner notes.
3. Gemini selects 3–7 tasks and writes a specific 2–3 sentence explanation for each, referencing the breed, age, and owner notes directly.
4. Each recommendation indicates whether it was driven by breed data, owner notes, or both.
5. Recommended tasks appear as expandable cards; clicking **Add to Schedule** inserts them into the task list.

Pet notes are validated before being sent to the AI — notes containing prompt-injection patterns are rejected with a warning.

---

## Sample Tasks

Ten built-in tasks are available in `constants/sample_tasks.py`:

| Task                  | Duration | Priority | Category   |
|-----------------------|----------|----------|------------|
| Morning walk          | 30 min   | HIGH     | exercise   |
| Breakfast feeding     | 10 min   | HIGH     | feeding    |
| Evening walk          | 30 min   | HIGH     | exercise   |
| Dinner feeding        | 10 min   | HIGH     | feeding    |
| Vet medication        | 5 min    | HIGH     | health     |
| Brushing/grooming     | 15 min   | MEDIUM   | grooming   |
| Playtime              | 20 min   | MEDIUM   | enrichment |
| Training session      | 15 min   | MEDIUM   | training   |
| Litter box cleanup    | 10 min   | LOW      | hygiene    |
| Socialisation/cuddles | 20 min   | LOW      | enrichment |

---

## Valid Input Ranges

| Field             | Valid Values                         |
|-------------------|--------------------------------------|
| Available minutes | 30 – 840 (30 min to 14 hours)        |
| Task duration     | 1+ minutes                           |
| Species           | dog, cat, rabbit, bird, other        |
| Priority          | low, medium, high (case-insensitive) |
| Pet notes         | Up to 1000 characters                |
