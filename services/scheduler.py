from models.owner import Owner
from models.pet import Pet
from models.task import Task, ScheduledTask


class Scheduler:
    def __init__(
        self,
        owner: Owner,
        pet: Pet,
        day_start_minute: int = 480,
        day_end_minute: int = 1320,
    ):
        self.owner = owner
        self.pet = pet
        self.day_start_minute = day_start_minute
        self.day_end_minute = day_end_minute
        self._tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        self._tasks.append(task)

    def remove_task(self, title: str) -> None:
        self._tasks = [t for t in self._tasks if t.title != title]

    def generate_plan(self) -> tuple[list[ScheduledTask], list[Task]]:
        active = [t for t in self._tasks if not t.completed]
        sorted_tasks = sorted(active, key=lambda t: t.priority.value, reverse=True)

        available_window = min(
            self.owner.available_minutes,
            self.day_end_minute - self.day_start_minute,
        )

        scheduled: list[ScheduledTask] = []
        skipped: list[Task] = []
        current_minute = self.day_start_minute
        remaining = available_window

        for task in sorted_tasks:
            if task.duration_minutes <= remaining:
                start = current_minute
                end = current_minute + task.duration_minutes
                scheduled.append(
                    ScheduledTask(
                        task=task,
                        start_time=self._minutes_to_time(start),
                        end_time=self._minutes_to_time(end),
                        reason=self._build_reason(task, scheduled),
                    )
                )
                current_minute = end
                remaining -= task.duration_minutes
            else:
                skipped.append(task)

        return scheduled, skipped

    def _minutes_to_time(self, minutes: int) -> str:
        hours, mins = divmod(minutes, 60)
        return f"{hours:02d}:{mins:02d}"

    def _build_reason(self, task: Task, already_scheduled: list[ScheduledTask]) -> str:
        label = task.priority.name.capitalize()
        if not already_scheduled:
            return f"{label} priority — scheduled first to ensure it gets done."
        prev = already_scheduled[-1]
        return f"{label} priority — follows {prev.task.title} at {prev.end_time}."
