from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from itertools import combinations
from typing import List, Optional, Tuple
from enum import Enum

_FREQUENCY_DELTAS = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
}


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
    start_time: Optional[str] = None  # preferred start time in "HH:MM" format
    frequency: Optional[str] = None  # "daily" or "weekly"
    due_date: Optional[date] = None
    notes: Optional[str] = None
    location: Optional[str] = None
    completed: bool = False

    def mark_complete(self) -> Optional['Task']:
        """Mark this task as completed.

        If the task is recurring, returns a new Task for the next occurrence
        with completed=False and due_date advanced by the frequency interval.
        Returns None for non-recurring tasks or if already completed.
        """
        if self.completed:
            return None

        self.completed = True

        if self.frequency is None:
            return None
        delta = _FREQUENCY_DELTAS.get(self.frequency)
        if delta is None:
            raise ValueError(f"Unknown frequency '{self.frequency}'. Use {list(_FREQUENCY_DELTAS)}.")

        base = self.due_date or date.today()
        return replace(self, completed=False, due_date=base + delta)


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

    def complete_task(self, title: str) -> Optional[Task]:
        """Mark the first incomplete task matching title as done.

        If it is recurring, the next occurrence is appended to this pet's task list.
        Returns the next occurrence Task, or None if not recurring / not found.
        """
        for task in self.tasks:
            if task.title == title and not task.completed:
                next_task = task.mark_complete()
                if next_task:
                    self.tasks.append(next_task)
                return next_task
        return None

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

    def _get_tasks(self, pet_name: Optional[str]) -> Tuple[Optional[Pet], List[Task]]:
        """Resolve a pet name to its (pet, tasks) pair, or return (None, all tasks)."""
        if pet_name:
            pet = self.owner.get_pet(pet_name)
            return pet, (pet.tasks if pet else [])
        pet = self.owner.pets[0] if len(self.owner.pets) == 1 else None
        return pet, self.owner.get_all_tasks()

    def _sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by ascending start_time; tasks without a time sort last.
        Ties broken by descending priority, then ascending duration."""
        return sorted(
            tasks,
            key=lambda t: (t.start_time or "99:99", -t.priority.value, t.duration_minutes),
        )

    def find_conflicts(self, pet_name: Optional[str] = None) -> List[str]:
        """Return warning strings for any incomplete tasks whose time intervals overlap.

        Tasks without a start_time or with an unreadable start_time are skipped silently.
        Pass pet_name to limit the check to a single pet's tasks.
        """
        _, tasks = self._get_tasks(pet_name)

        def to_mins(time_str: str) -> Optional[int]:
            try:
                h, m = time_str.split(":")
                return int(h) * 60 + int(m)
            except (ValueError, AttributeError):
                return None

        timed = [(t, to_mins(t.start_time)) for t in tasks if t.start_time and not t.completed]
        timed = [(t, mins) for t, mins in timed if mins is not None]

        warnings = []
        for (a, a_start), (b, b_start) in combinations(timed, 2):
            overlap = min(a_start + a.duration_minutes, b_start + b.duration_minutes) - max(a_start, b_start)
            if overlap > 0:
                warnings.append(
                    f"WARNING: '{a.title}' ({a.start_time}) and "
                    f"'{b.title}' ({b.start_time}) overlap by {overlap} min"
                )
        return warnings

    def _fits_in_budget(self, task: Task, remaining_minutes: int) -> bool:
        """Return True if the task fits within the remaining time budget."""
        return task.duration_minutes <= remaining_minutes

    def generate_plan(self, pet_name: Optional[str] = None, start_time: str = "08:00") -> 'Plan':
        """Build a scheduled Plan for one pet or all pets within the owner's available time.

        2a. Algorithm
            Tasks are sorted by preferred start_time, then scheduled one by one
            against the owner's available_minutes budget. Each task is either
            added to the plan or skipped — there is no backtracking.

        2b. Tradeoffs
            This is a greedy algorithm: tasks are committed to in sort order
            and a skipped task is never reconsidered, even if later tasks are
            small enough to fill the remaining budget.

            Example — budget = 20 min, three tasks sorted by start_time:
              A: 15 min  HIGH      B: 10 min  MEDIUM      C: 10 min  LOW

              Greedy result:  schedules A (15 min used, 5 remaining),
                              skips B (10 > 5), skips C (10 > 5)  →  15/20 min used.

              Optimal result: schedules B + C = 20 min  →  20/20 min used,
                              but this skips the HIGH priority task A entirely.

            In a care app, scheduling A is usually the right call — a pet's
            medication should not be dropped to squeeze in two grooming tasks.
            The greedy approach aligns with that intent by respecting sort order
            (priority, then time) over raw budget utilisation.

            The alternative — finding the highest-value combination — is the
            0/1 knapsack problem, solved in O(n × W) with dynamic programming.
            For under 20 tasks this makes no practical difference in outcome,
            and the greedy loop is far easier to read and explain.
        """
        pet, tasks = self._get_tasks(pet_name)
        sorted_tasks = self._sort_tasks([t for t in tasks if not t.completed])
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
            warnings=self.find_conflicts(pet_name),
        )


class Plan:
    def __init__(
        self,
        scheduled_tasks: List[Task],
        skipped_tasks: List[Task],
        start_time: str,
        owner: Owner,
        pet: Optional[Pet],
        warnings: Optional[List[str]] = None,
    ):
        self.scheduled_tasks = scheduled_tasks
        self.skipped_tasks = skipped_tasks
        self.start_time = start_time
        self.owner = owner
        self.pet = pet
        self.warnings = warnings or []

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

        if self.warnings:
            lines.append("\nSchedule warnings:")
            for w in self.warnings:
                lines.append(f"  {w}")

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
