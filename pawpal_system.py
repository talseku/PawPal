from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority
    category: Optional[str] = None
    time_of_day: Optional[str] = None
    recurring: bool = False
    notes: Optional[str] = None
    location: Optional[str] = None
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True


@dataclass
class Pet:
    name: str
    age: float
    species: str
    breed: Optional[str] = None
    weight: Optional[float] = None
    medical_notes: Optional[str] = None
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove all tasks matching the given title."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def get_tasks_by_priority(self, priority: Priority) -> List[Task]:
        """Return all tasks matching the given priority level."""
        return [t for t in self.tasks if t.priority == priority]

    def is_senior(self) -> bool:
        """Return True if the pet is considered senior for its species."""
        if self.species == "dog":
            return self.age > 10
        if self.species == "cat":
            return self.age > 12
        return False

    def is_young(self) -> bool:
        """Return True if the pet is under one year old."""
        return self.age < 1


@dataclass
class Owner:
    name: str
    available_minutes: int
    phone: Optional[str] = None
    email: Optional[str] = None
    pet_insurance: Optional[str] = None
    preferences: List[str] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pet list."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove all pets matching the given name."""
        self.pets = [p for p in self.pets if p.name != name]

    def get_pet(self, name: str) -> Optional[Pet]:
        """Return the first pet matching the given name, or None."""
        for pet in self.pets:
            if pet.name == name:
                return pet
        return None

    def get_all_tasks(self) -> List[Task]:
        """Return a flat list of all tasks across every pet."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner

    def _sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by descending priority, then ascending duration."""
        # Primary: priority descending (HIGH=3 first)
        # Secondary: duration ascending (shorter first to fit more tasks)
        # Tertiary: insertion order preserved by stable sort
        return sorted(tasks, key=lambda t: (-t.priority.value, t.duration_minutes))

    def _fits_in_budget(self, task: Task, remaining_minutes: int) -> bool:
        """Return True if the task fits within the remaining time budget."""
        return task.duration_minutes <= remaining_minutes

    def generate_plan(self, pet_name: Optional[str] = None, start_time: str = "08:00") -> 'Plan':
        """Build a scheduled Plan for one pet or all pets within the owner's available time."""
        if pet_name:
            pet = self.owner.get_pet(pet_name)
            tasks = pet.tasks if pet else []
        else:
            pet = self.owner.pets[0] if len(self.owner.pets) == 1 else None
            tasks = self.owner.get_all_tasks()

        sorted_tasks = self._sort_tasks(tasks)
        remaining = self.owner.available_minutes
        scheduled: List[Task] = []
        skipped: List[Task] = []

        for task in sorted_tasks:
            if self._fits_in_budget(task, remaining):
                scheduled.append(task)
                remaining -= task.duration_minutes
            else:
                skipped.append(task)

        return Plan(
            scheduled_tasks=scheduled,
            skipped_tasks=skipped,
            start_time=start_time,
            owner=self.owner,
            pet=pet,
        )


class Plan:
    def __init__(
        self,
        scheduled_tasks: List[Task],
        skipped_tasks: List[Task],
        start_time: str,
        owner: Owner,
        pet: Optional[Pet],
    ):
        self.scheduled_tasks = scheduled_tasks
        self.skipped_tasks = skipped_tasks
        self.start_time = start_time
        self.owner = owner
        self.pet = pet

    def explain(self) -> str:
        """Return a human-readable summary of the scheduled and skipped tasks."""
        pet_label = self.pet.name if self.pet else "all pets"
        lines = [f"{self.owner.name}'s care plan for {pet_label} (starting {self.start_time}):\n"]

        if not self.scheduled_tasks:
            lines.append("No tasks could be scheduled within the available time.")
        else:
            lines.append("Scheduled tasks:")
            for task in self.scheduled_tasks:
                lines.append(
                    f"  - {task.title} ({task.duration_minutes} min, {task.priority.name} priority)"
                )

        if self.skipped_tasks:
            lines.append("\nSkipped tasks:")
            for task in self.skipped_tasks:
                lines.append(f"  - {task.title} ({task.duration_minutes} min) — insufficient time remaining")

            high_skipped = [t for t in self.skipped_tasks if t.priority == Priority.HIGH]
            if high_skipped:
                names = ", ".join(t.title for t in high_skipped)
                lines.append(f"\n  WARNING: High-priority task(s) could not be scheduled: {names}")

        total = sum(t.duration_minutes for t in self.scheduled_tasks)
        lines.append(f"\nTotal time scheduled: {total} min of {self.owner.available_minutes} min available.")
        return "\n".join(lines)

    def to_table(self) -> List[dict]:
        """Return the plan as a list of dicts suitable for tabular display."""
        rows = []
        current_minutes = self._time_to_minutes(self.start_time)

        for task in self.scheduled_tasks:
            start = self._minutes_to_time(current_minutes)
            end = self._minutes_to_time(current_minutes + task.duration_minutes)
            rows.append({
                "title": task.title,
                "priority": task.priority.name,
                "category": task.category or "—",
                "duration_min": task.duration_minutes,
                "start": start,
                "end": end,
                "location": task.location or "—",
                "status": "scheduled",
            })
            current_minutes += task.duration_minutes

        for task in self.skipped_tasks:
            rows.append({
                "title": task.title,
                "priority": task.priority.name,
                "category": task.category or "—",
                "duration_min": task.duration_minutes,
                "start": "—",
                "end": "—",
                "location": task.location or "—",
                "status": "skipped",
            })

        return rows

    @staticmethod
    def _time_to_minutes(time_str: str) -> int:
        """Convert a 'HH:MM' string to total minutes since midnight."""
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes

    @staticmethod
    def _minutes_to_time(total_minutes: int) -> str:
        """Convert total minutes since midnight to a 'HH:MM' string."""
        hours = (total_minutes // 60) % 24
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"
