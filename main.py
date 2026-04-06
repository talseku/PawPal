from pawpal_system import Owner, Pet, Task, Scheduler, Priority

# ── Pets ──────────────────────────────────────────────────────────
mochi = Pet(name="Mochi", age=3, species="dog", breed="Shiba Inu")
luna = Pet(name="Luna", age=7, species="cat", medical_notes="on thyroid meds")

# ── Tasks for Mochi ───────────────────────────────────────────────
mochi.add_task(Task(
    title="Morning walk",
    duration_minutes=30,
    priority=Priority.HIGH,
    category="exercise",
    time_of_day="morning",
    location="park",
))
mochi.add_task(Task(
    title="Breakfast",
    duration_minutes=10,
    priority=Priority.HIGH,
    category="feeding",
    time_of_day="morning",
))
mochi.add_task(Task(
    title="Afternoon play session",
    duration_minutes=20,
    priority=Priority.MEDIUM,
    category="enrichment",
    time_of_day="afternoon",
    location="home",
))

# ── Tasks for Luna ────────────────────────────────────────────────
luna.add_task(Task(
    title="Administer thyroid medication",
    duration_minutes=5,
    priority=Priority.HIGH,
    category="medication",
    time_of_day="morning",
    notes="Mix with small amount of wet food",
))
luna.add_task(Task(
    title="Brush coat",
    duration_minutes=15,
    priority=Priority.LOW,
    category="grooming",
    time_of_day="evening",
))
luna.add_task(Task(
    title="Dinner",
    duration_minutes=10,
    priority=Priority.HIGH,
    category="feeding",
    time_of_day="evening",
))

# ── Owner ─────────────────────────────────────────────────────────
jordan = Owner(
    name="Jordan",
    available_minutes=90,
    preferences=["prefers morning tasks"],
)
jordan.add_pet(mochi)
jordan.add_pet(luna)

# ── Schedule ──────────────────────────────────────────────────────
scheduler = Scheduler(owner=jordan)
plan = scheduler.generate_plan(start_time="08:00")

W = 60  # total display width

def divider(char="-"):
    print(char * W)

def section(title):
    divider("=")
    print(f"  {title}")

# ── Header ────────────────────────────────────────────────────────
section("TODAY'S SCHEDULE")
pets_label = ", ".join(p.name for p in jordan.pets)
print(f"  Owner : {jordan.name}")
print(f"  Pets  : {pets_label}")
print(f"  Budget: {jordan.available_minutes} min  |  Start: 08:00")
divider("=")

# ── Scheduled tasks table ─────────────────────────────────────────
scheduled = [r for r in plan.to_table() if r["status"] == "scheduled"]
skipped   = [r for r in plan.to_table() if r["status"] == "skipped"]

if scheduled:
    print(f"\n  {'TASK':<30} {'CAT':<12} {'START':>5}  {'END':>5}  {'MIN':>4}  PRIORITY")
    divider()
    for row in scheduled:
        print(
            f"  {row['title']:<30} {row['category']:<12}"
            f" {row['start']:>5}  {row['end']:>5}  {row['duration_min']:>3}m"
            f"  {row['priority']}"
        )
    total = sum(r["duration_min"] for r in scheduled)
    divider()
    print(f"  {len(scheduled)} task(s) scheduled  |  {total} of {jordan.available_minutes} min used")
else:
    print("\n  No tasks could be scheduled within the available time.")

# ── Skipped tasks ─────────────────────────────────────────────────
if skipped:
    print(f"\n  SKIPPED ({len(skipped)} task(s) — insufficient time)")
    divider()
    for row in skipped:
        print(f"  {row['title']:<30} {row['duration_min']:>3} min  {row['priority']}")

# ── Warnings ──────────────────────────────────────────────────────
high_skipped = [r for r in skipped if r["priority"] == "HIGH"]
if high_skipped:
    print()
    print("  ! WARNING: the following HIGH priority tasks were not scheduled:")
    for row in high_skipped:
        print(f"    - {row['title']}")

divider("=")
