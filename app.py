import streamlit as st

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
)
from constants.sample_tasks import SAMPLE_TASKS

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Plan and schedule daily pet care tasks.")

if "tasks" not in st.session_state:
    st.session_state["tasks"] = []

# ── Owner & Pet ──────────────────────────────────────────────────────────────
st.header("Owner & Pet")
col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Your name", value="Alex")
    available_minutes = st.number_input(
        "Available minutes today", min_value=30, max_value=840, value=480, step=10
    )
with col2:
    pet_name = st.text_input("Pet's name", value="Buddy")
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    pet_age = st.number_input("Pet's age (years)", min_value=0, max_value=30, value=2)

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
        st.write(
            f"{i + 1}. **{t['title']}** — {t['duration_minutes']} min | "
            f"{t['priority'].upper()} | {t['category']}"
        )
    if st.button("Clear all tasks"):
        st.session_state["tasks"] = []
        st.rerun()

# ── Generate Schedule ────────────────────────────────────────────────────────
st.header("Generate Schedule")
if st.button("Generate Schedule", type="primary"):
    if not st.session_state["tasks"]:
        st.warning("Add at least one task before generating a schedule.")
    else:
        try:
            validated_minutes = validate_available_minutes(int(available_minutes))
            validated_species = validate_species(species)
            owner = Owner(name=owner_name.strip() or "Owner", available_minutes=validated_minutes)
            pet = Pet(name=pet_name.strip() or "Pet", species=validated_species, age=int(pet_age))
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
