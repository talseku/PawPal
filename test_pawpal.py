from pawpal_system import Task, Pet, Priority


def test_mark_complete_sets_completed_to_true():
    task = Task(title="Feed", duration_minutes=5, priority=Priority.HIGH)
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", age=3, species="dog")
    task = Task(title="Walk", duration_minutes=30, priority=Priority.MEDIUM)
    pet.add_task(task)
    assert len(pet.tasks) == 1
