from dataclasses import dataclass
from models.priority import Priority


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority
    category: str = "general"
    completed: bool = False

    def mark_complete(self) -> None:
        self.completed = True


@dataclass
class ScheduledTask:
    task: Task
    start_time: str
    end_time: str
    reason: str = ""
