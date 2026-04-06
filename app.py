import streamlit as st
from pawpal_system import Owner, Pet, Task, Priority, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Session state ──────────────────────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = None
if "active_pet_name" not in st.session_state:
    st.session_state.active_pet_name = None

# ── 1. Owner setup ─────────────────────────────────────────────────────────────
st.subheader("Owner Info")

with st.form("owner_form"):
    owner_name     = st.text_input("Owner name", value="Jordan")
    available_mins = st.number_input("Available time (minutes)", min_value=10, max_value=480, value=120)
    save_owner     = st.form_submit_button("Save Owner")

if save_owner:
    st.session_state.owner = Owner(name=owner_name, available_minutes=int(available_mins))
    st.session_state.active_pet_name = None
    st.success(f"Owner '{owner_name}' saved.")

if st.session_state.owner is None:
    st.info("Set up an owner above to get started.")
    st.stop()

owner: Owner = st.session_state.owner

st.divider()

# ── 2. Add a Pet ───────────────────────────────────────────────────────────────
st.subheader("Pets")

with st.form("add_pet_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        pet_age = st.number_input("Age (years)", min_value=0.0, max_value=30.0, value=3.0, step=0.5)
    with col3:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    add_pet = st.form_submit_button("Add Pet")

if add_pet:
    if owner.get_pet(pet_name):                         # owner.get_pet() — avoid duplicates
        st.warning(f"A pet named '{pet_name}' already exists.")
    else:
        new_pet = Pet(name=pet_name, age=pet_age, species=species)
        owner.add_pet(new_pet)                          # owner.add_pet()
        st.session_state.active_pet_name = new_pet.name
        st.success(f"Added: {pet_name}")

if not owner.pets:
    st.info("Add a pet above to continue.")
    st.stop()

# Pet selector — persisted so switching pets survives reruns.
pet_names = [p.name for p in owner.pets]
if st.session_state.active_pet_name not in pet_names:
    st.session_state.active_pet_name = pet_names[0]

selected = st.radio("Active pet", pet_names, horizontal=True,
                    index=pet_names.index(st.session_state.active_pet_name))
st.session_state.active_pet_name = selected

pet: Pet = owner.get_pet(st.session_state.active_pet_name)  # owner.get_pet()

# Pet status badges from pawpal_system methods.
if pet.is_senior():                                     # pet.is_senior()
    st.info(f"{pet.name} is a senior {pet.species}.")
elif pet.is_young():                                    # pet.is_young()
    st.info(f"{pet.name} is under 1 year old.")

st.divider()

# ── 3. Task management ─────────────────────────────────────────────────────────
st.subheader(f"Tasks for {pet.name}")

with st.form("task_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority_str = st.selectbox("Priority", ["LOW", "MEDIUM", "HIGH"], index=2)
    add_task = st.form_submit_button("Add Task")

if add_task:
    task = Task(
        title=task_title,
        duration_minutes=int(duration),
        priority=Priority[priority_str],
    )
    pet.add_task(task)                                  # pet.add_task()
    st.success(f"Added: {task_title}")

if pet.tasks:
    st.write(f"**{pet.name}'s tasks:**")

    header = st.columns([3, 2, 2, 2])
    header[0].markdown("**Task**")
    header[1].markdown("**Duration**")
    header[2].markdown("**Priority**")
    header[3].markdown("**Status**")

    for task in pet.tasks:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        col1.write(task.title)
        col2.write(f"{task.duration_minutes} min")
        col3.write(task.priority.name)
        if task.completed:
            col4.write("Done")
        else:
            if col4.button("Mark done", key=f"done_{task.title}"):
                task.mark_complete()                    # task.mark_complete()
                st.rerun()

    st.caption("Remove a task:")
    remove_title = st.selectbox("Select task", options=[t.title for t in pet.tasks])
    if st.button("Remove task"):
        pet.remove_task(remove_title)                   # pet.remove_task()
        st.rerun()
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ── 4. Schedule generation ─────────────────────────────────────────────────────
st.subheader("Generate Schedule")

start_time  = st.text_input("Start time (HH:MM)", value="08:00")
schedule_all = (
    st.checkbox("Schedule all pets", value=False)
    if len(owner.pets) > 1 else False
)

if st.button("Generate schedule"):
    tasks_to_check = owner.get_all_tasks() if schedule_all else pet.tasks  # owner.get_all_tasks()
    if not tasks_to_check:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(owner)
        plan = scheduler.generate_plan(                 # Scheduler.generate_plan()
            pet_name=None if schedule_all else pet.name,
            start_time=start_time,
        )

        st.markdown("### Plan")
        st.text(plan.explain())                         # plan.explain()

        st.markdown("### Schedule table")
        st.table(plan.to_table())                       # plan.to_table()