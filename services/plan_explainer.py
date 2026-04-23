from models.task import ScheduledTask, Task
from models.owner import Owner
from models.pet import Pet

_PRIORITY_EMOJI = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}


class PlanExplainer:
    def __init__(
        self,
        scheduled_tasks: list[ScheduledTask],
        skipped_tasks: list[Task],
        owner: Owner,
        pet: Pet,
    ):
        self.scheduled_tasks = scheduled_tasks
        self.skipped_tasks = skipped_tasks
        self.owner = owner
        self.pet = pet
        self.total_minutes_scheduled = sum(
            st.task.duration_minutes for st in scheduled_tasks
        )

    def summarize(self) -> str:
        count = len(self.scheduled_tasks)
        skipped = len(self.skipped_tasks)
        hours, mins = divmod(self.total_minutes_scheduled, 60)
        time_str = f"{hours}h {mins}m" if hours else f"{mins}m"
        return (
            f"## {self.pet.name}'s Daily Schedule\n"
            f"**Owner:** {self.owner.name} | "
            f"**Available:** {self.owner.available_minutes} min | "
            f"**Scheduled:** {count} task(s) ({time_str}) | "
            f"**Skipped:** {skipped} task(s)"
        )

    def explain_task(self, st: ScheduledTask) -> str:
        emoji = _PRIORITY_EMOJI.get(st.task.priority.name, "⚪")
        return (
            f"**{st.start_time} – {st.end_time}** | "
            f"{emoji} {st.task.title} "
            f"({st.task.duration_minutes} min, {st.task.category})\n"
            f"> {st.reason}"
        )

    def explain_skipped(self) -> str:
        if not self.skipped_tasks:
            return ""
        lines = [
            "---",
            "### Skipped Tasks",
            "_These tasks didn't fit in the available time window:_",
        ]
        for task in self.skipped_tasks:
            lines.append(
                f"- ~~{task.title}~~ ({task.duration_minutes} min, {task.priority.name} priority)"
            )
        return "\n".join(lines)
