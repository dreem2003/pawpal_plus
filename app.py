import os

import streamlit as st


from dotenv import load_dotenv
load_dotenv()

from constants.breed_options import BREED_OPTIONS
from constants.sample_tasks import SAMPLE_TASKS
from models.owner import Owner
from models.pet import Pet
from models.task import Task
from services.scheduler import Scheduler
from services.plan_explainer import PlanExplainer
from utils.validators import (
    validate_available_minutes,
    validate_duration,
    validate_species,
    parse_priority,
    validate_pet_notes,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Plan and schedule daily pet care tasks.")

if "tasks" not in st.session_state:
    st.session_state["tasks"] = []
if "ai_recs" not in st.session_state:
    st.session_state["ai_recs"] = None
if "ai_error" not in st.session_state:
    st.session_state["ai_error"] = None

# ── Owner & Pet ──────────────────────────────────────────────────────────────
st.header("Owner & Pet")
col1, col2 = st.columns(2)

with col1:
    first_name = st.text_input("First name", value="Derek")
    last_name = st.text_input("Last name", value="Anozie")
    st.markdown("**Daily available time**")
    tc1, tc2 = st.columns(2)
    with tc1:
        avail_hours = st.number_input("Hours", min_value=0, max_value=14, value=8, step=1)
    with tc2:
        avail_mins_extra = st.number_input("Minutes", min_value=0, max_value=59, value=0, step=5)
    available_minutes = int(avail_hours) * 60 + int(avail_mins_extra)

with col2:
    pet_name = st.text_input("Pet's name", value="Simba")
    species = st.selectbox(
        "Species", ["-- Select species --", "dog", "cat", "rabbit", "bird", "other"]
    )
    species_chosen = species != "-- Select species --"
    breed_list = BREED_OPTIONS.get(species, []) if species_chosen else ["Select a species first"]
    breed = st.selectbox("Breed", breed_list, disabled=not species_chosen)
    pet_age = st.number_input("Pet's age (years)", min_value=0, max_value=30, value=2)

pet_notes = st.text_area(
    "About your pet",
    placeholder=(
        "Describe your pet's favourite activities, specific needs, training goals, "
        "health considerations, or anything else that should shape their daily plan..."
    ),
    height=150,
)

# ── AI Task Recommendations ───────────────────────────────────────────────────
st.header("AI Task Recommendations")

_api_key = os.getenv("GEMINI_API_KEY", "")
if not _api_key:
    st.info(
        "Add a `GEMINI_API_KEY` to a `.env` file in this folder to enable "
        "AI-powered task recommendations tailored to your pet."
    )
else:
    _notes_ready = bool(pet_notes.strip()) and species_chosen
    if not _notes_ready:
        st.caption("Select a species and add notes about your pet to unlock recommendations.")

    if st.button("Get AI Recommendations", disabled=not _notes_ready):
        st.session_state["ai_recs"] = None
        st.session_state["ai_error"] = None
        try:
            sanitised_notes, note_warnings = validate_pet_notes(pet_notes)
            for w in note_warnings:
                st.warning(w)

            from services.ai_recommender import PetAIRecommender
            _pet_for_ai = Pet(
                name=pet_name.strip() or "Pet",
                species=species,
                age=int(pet_age),
                breed=breed,
                notes=sanitised_notes,
            )
            with st.spinner("Consulting the AI pet care specialist..."):
                _recommender = PetAIRecommender(api_key=_api_key)
                _result = _recommender.get_recommendations(_pet_for_ai, sanitised_notes)
            st.session_state["ai_recs"] = _result
            if _result.error:
                st.session_state["ai_error"] = _result.error
        except ValueError as e:
            st.session_state["ai_error"] = str(e)
        except RuntimeError as e:
            st.session_state["ai_error"] = str(e)

    if st.session_state["ai_error"]:
        st.error(st.session_state["ai_error"])

    _result = st.session_state["ai_recs"]
    if _result and _result.recommendations:
        _display_name = pet_name.strip() or "your pet"
        st.success(
            f"Found {len(_result.recommendations)} recommended tasks for {_display_name}!"
        )

        if _result.summary:
            with st.expander("Why these tasks?", expanded=True):
                st.write(_result.summary)

        _basis_labels = {
            "breed_data": "Breed data",
            "owner_notes": "Your notes",
            "both": "Breed data + your notes",
        }
        for _rec in _result.recommendations:
            with st.container(border=True):
                _col_info, _col_btn = st.columns([8, 2])
                with _col_info:
                    st.markdown(
                        f"**{_rec.title}** &nbsp; `{_rec.priority.upper()}` &nbsp; "
                        f"_{_rec.category}_ &nbsp; {_rec.duration_minutes} min"
                    )
                    st.caption(
                        f"**Why:** {_rec.reason}  \n"
                        f"*Source: {_basis_labels.get(_rec.basis, _rec.basis)}*"
                    )
                with _col_btn:
                    _already = any(
                        t["title"] == _rec.title for t in st.session_state["tasks"]
                    )
                    if _already:
                        st.button(
                            "Added",
                            key=f"ai_add_{_rec.title}",
                            disabled=True,
                        )
                    elif st.button("Add to Schedule", key=f"ai_add_{_rec.title}"):
                        st.session_state["tasks"].append({
                            "title": _rec.title,
                            "duration_minutes": _rec.duration_minutes,
                            "priority": _rec.priority,
                            "category": _rec.category,
                        })
                        st.rerun()

# ── Task Input ───────────────────────────────────────────────────────────────
st.header("Add Care Tasks")

with st.expander("Load sample tasks"):
    if st.button("Load 10 sample tasks"):
        st.session_state["tasks"] = list(SAMPLE_TASKS)
        st.success("Sample tasks loaded!")

with st.form("task_form", clear_on_submit=True):
    task_title = st.text_input("Task title")
    col3, col4, col5 = st.columns(3)
    with col3:
        task_duration = st.number_input("Duration (min)", min_value=1, max_value=480, value=15)
    with col4:
        task_priority = st.selectbox("Priority", ["high", "medium", "low"])
    with col5:
        task_category = st.text_input("Category", value="general")
    submitted = st.form_submit_button("Add Task")
    if submitted:
        if not task_title.strip():
            st.error("Task title cannot be empty.")
        else:
            st.session_state["tasks"].append(
                {
                    "title": task_title.strip(),
                    "duration_minutes": int(task_duration),
                    "priority": task_priority,
                    "category": task_category.strip() or "general",
                }
            )
            st.success(f"Added: {task_title.strip()}")

if st.session_state["tasks"]:
    st.subheader(f"Tasks ({len(st.session_state['tasks'])})")
    for i, t in enumerate(st.session_state["tasks"]):
        col_info, col_del = st.columns([9, 1])
        with col_info:
            st.write(
                f"{i + 1}. **{t['title']}** — {t['duration_minutes']} min | "
                f"{t['priority'].upper()} | {t['category']}"
            )
        with col_del:
            if st.button("✕", key=f"del_{i}", help="Remove this task"):
                st.session_state["tasks"].pop(i)
                st.rerun()
    if st.button("Clear all tasks"):
        st.session_state["tasks"] = []
        st.rerun()

# ── Generate Schedule ────────────────────────────────────────────────────────
st.header("Generate Schedule")
if st.button("Generate Schedule", type="primary"):
    if not st.session_state["tasks"]:
        st.warning("Add at least one task before generating a schedule.")
    elif not species_chosen:
        st.warning("Please select a species for your pet.")
    elif available_minutes < 30:
        st.error("Please enter at least 30 minutes of available time.")
    elif available_minutes > 840:
        st.error("Available time cannot exceed 14 hours (840 minutes).")
    else:
        try:
            validated_minutes = validate_available_minutes(available_minutes)
            validated_species = validate_species(species)
            owner_name = f"{first_name.strip()} {last_name.strip()}".strip() or "Owner"
            owner = Owner(name=owner_name, available_minutes=validated_minutes)
            pet = Pet(
                name=pet_name.strip() or "Pet",
                species=validated_species,
                age=int(pet_age),
                breed=breed,
                notes=pet_notes.strip(),
            )
            scheduler = Scheduler(owner, pet)

            for entry in st.session_state["tasks"]:
                try:
                    task = Task(
                        title=entry["title"],
                        duration_minutes=validate_duration(entry["duration_minutes"]),
                        priority=parse_priority(entry["priority"]),
                        category=entry.get("category", "general"),
                    )
                    scheduler.add_task(task)
                except ValueError as e:
                    st.warning(f"Skipping '{entry['title']}': {e}")

            scheduled, skipped = scheduler.generate_plan()
            explainer = PlanExplainer(scheduled, skipped, owner, pet)

            st.markdown(explainer.summarize())
            st.divider()
            for st_task in scheduled:
                st.markdown(explainer.explain_task(st_task))
            if skipped:
                st.markdown(explainer.explain_skipped())

        except ValueError as e:
            st.error(str(e))
