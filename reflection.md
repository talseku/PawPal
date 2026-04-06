# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**
Three core actions users should be able to perform include adding a task, generating a schedule, and viewing the schedule as a table.
To do this, my UML design includes the Owner class, which contains personal information, time details, and preferences, and the Pet class, which contains necessary information about the owner's pet.
Additionally, my UML design introduces an enumerated Priority class for ranking the Tasks. Besides priority, tasks contain their name, category, notes, and scheduling metadata. The Scheduler takes the owner, pet, and tasks, runs a greedy algorithm to maximize the amount and priority of tasks within an owner's time allowance, and returns a Plan containing a list of tasks that were scheduled, tasks that were skipped, and methods to explain and display the plan.

**b. Design changes**
Based on the AI feedback, I added a direct mapping of priority strings to integer values, included default values for opetional fields, included owner and pet as kind of foreign keys in the plan class to be used in the explaining function, and modified the Owner class to use the @dataclass structure to be consistent with the Pet class.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**
The constraints that my scheduler accounts for include task priority as well as time/duration/conflicts.
To decide which constraints mattered most, I considered the application's context from the user's perspective. If I were attempting to prioritize and schedule pet care for my pets, I would first want to address the most critical tasks that can not be skipped. Then, I might want to complete as many small tasks as possible, to leave long, unimportant tasks for last.

**b. Tradeoffs**
One of the tradeoffs my scheduler makes is that some tasks are skipped in the scheduling process when they do not fit into the schedule (even though they might if the schedule was rearranged). In my opinion, this tradeoff is reasonable in this scenario because it naturally makes more sense for humans to plan their days by scheduling tasks in sequential order, even if it means that the schedule isn't the 100% most time-efficient.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
