import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

from models.pet import Pet

GEMINI_MODEL = "gemini-2.5-flash"

_BREED_PATTERN = re.compile(r'\("([^"]+)",\s*(high|medium|low)\)')
_PRIORITY_VALUES = {"high": 3, "medium": 2, "low": 1}
_STOP_WORDS = {
    "the", "and", "for", "are", "but", "not", "you", "all", "can", "has",
    "was", "one", "our", "out", "get", "him", "his", "how", "its", "may",
    "new", "now", "old", "see", "two", "way", "who", "did", "she", "use",
    "with", "that", "this", "they", "have", "from", "been", "your", "very",
    "just", "also", "more", "over", "like", "some", "time", "than", "then",
    "when", "much", "too", "into", "will", "their", "there", "about",
}

_DEFAULT_CSV = Path(__file__).parent.parent / "constants" / "tasks.csv"


@dataclass
class TaskRecommendation:
    title: str
    category: str
    duration_minutes: int
    priority: str
    reason: str
    basis: str


@dataclass
class RecommendationResult:
    recommendations: list
    summary: str
    error: Optional[str] = None


def _load_tasks(csv_path: Path) -> list:
    tasks = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Header cells have trailing spaces — strip them so key lookups work
        reader.fieldnames = [h.strip() for h in reader.fieldnames]
        for row in reader:
            tasks.append({
                "title": row["title"].strip(),
                "duration_minutes": int(row["duration_minutes"].strip()),
                "category": row["category"].strip(),
                "viable_breeds": row["viable_breeds"].strip(),
            })
    return tasks


def _parse_viable_breeds(breeds_str: str) -> dict:
    return {name: priority for name, priority in _BREED_PATTERN.findall(breeds_str)}


def _extract_keywords(text: str) -> list:
    words = re.findall(r"[a-z]{3,}", text.lower())
    return [w for w in words if w not in _STOP_WORDS]


def _score_task(task: dict, breed: str, keywords: list) -> float:
    breeds = _parse_viable_breeds(task["viable_breeds"])
    breed_priority = breeds.get(breed) or breeds.get("Mixed / Other")
    if breed_priority is None:
        return 0.0
    base = float(_PRIORITY_VALUES.get(breed_priority, 0))
    combined = (task["title"] + " " + task["category"]).lower()
    boost = sum(0.4 for kw in keywords if kw in combined)
    return base + boost


def _strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"```(?:json)?\s*", "", text).strip()
    return text


class PetAIRecommender:
    def __init__(self, api_key: str, csv_path: Optional[Path] = None):
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is required to use AI recommendations.")
        self._client = genai.Client(api_key=api_key)
        self._tasks = _load_tasks(csv_path or _DEFAULT_CSV)

    def get_recommendations(
        self,
        pet: Pet,
        pet_notes: str,
        max_context_tasks: int = 15,
        max_recommendations: int = 7,
    ) -> RecommendationResult:
        keywords = _extract_keywords(pet_notes)

        scored = []
        for t in self._tasks:
            score = _score_task(t, pet.breed, keywords)
            if score > 0:
                scored.append((score, t))
        scored.sort(key=lambda x: x[0], reverse=True)
        top_tasks = [t for _, t in scored[:max_context_tasks]]

        if not top_tasks:
            return RecommendationResult(
                recommendations=[],
                summary="No tasks in the database match this breed.",
                error="No suitable tasks found for this breed.",
            )

        task_lines = "\n".join(
            f"- {t['title']} | {t['category']} | {t['duration_minutes']} min"
            for t in top_tasks
        )

        notes_section = pet_notes.strip() if pet_notes.strip() else "(No notes provided — use breed defaults.)"

        prompt = f"""You are a pet care specialist AI for PawPal+, an app that builds personalised daily care plans for pets.

You will receive:
- Details about a specific pet
- The owner's notes about their pet's preferences, health, and needs
- A curated list of care tasks from our database that are appropriate for this breed

Your job:
1. Recommend between 3 and {max_recommendations} tasks from the list that best match the pet's situation.
2. For each task, write a specific explanation (2-3 sentences) covering:
   - Why this task matters for THIS breed at THIS age
   - How the owner's notes make this task especially relevant or urgent
   - What benefit the pet will gain (physical, mental, social, or health)
3. If the owner's notes mention health conditions, flag which tasks directly support management of that condition.
4. If the notes mention favourite activities, prioritise tasks in related categories.

Pet Information:
- Name: {pet.name}
- Species: {pet.species}
- Breed: {pet.breed}
- Age: {pet.age} year(s)

Owner's Notes:
{notes_section}

Available Tasks from Database:
{task_lines}

Rules:
- Only recommend tasks from the list above. Do not invent task names.
- Each explanation must reference the pet specifically — avoid generic pet-care advice.
- Indicate for each task whether the selection was driven by breed data, owner notes, or both.
- Do not recommend more than {max_recommendations} tasks.

Respond in this exact JSON format (raw JSON only, no markdown code fences):
{{
  "recommendations": [
    {{
      "title": "<exact task title from list>",
      "priority": "<high|medium|low>",
      "reason": "<specific 2-3 sentence explanation for this pet>",
      "basis": "<breed_data|owner_notes|both>"
    }}
  ],
  "summary": "<2-3 sentence overview of the selection strategy for this pet>"
}}"""

        try:
            response = self._client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )
            data = json.loads(_strip_markdown_fences(response.text))
        except Exception as exc:
            return RecommendationResult(
                recommendations=[],
                summary="",
                error=f"AI service error: {exc}",
            )

        task_lookup = {t["title"]: t for t in top_tasks}

        recs = []
        for item in data.get("recommendations", []):
            title = item.get("title", "").strip()
            csv_task = task_lookup.get(title)
            if csv_task is None:
                continue  # model returned a task not in the provided list — discard
            recs.append(TaskRecommendation(
                title=title,
                category=csv_task["category"],
                duration_minutes=csv_task["duration_minutes"],
                priority=item.get("priority", "medium"),
                reason=item.get("reason", ""),
                basis=item.get("basis", "breed_data"),
            ))

        return RecommendationResult(
            recommendations=recs,
            summary=data.get("summary", ""),
        )
