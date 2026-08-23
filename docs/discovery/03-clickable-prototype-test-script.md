# ImpactOS — Clickable Prototype Test Script

**Prototype:** `docs/wireframes/impactos-wireframes.html`  
**Audience:** 5–8 students, 1–2 mentors, and at least 1 moderator/admin  
**Session:** 30–40 minutes  
**Data:** synthetic scenario only; never use a real sensitive report

## 1. Moderator setup

Before the session:

- open the HTML wireframe prototype;
- prepare the synthetic scenario below;
- confirm recording permission, if applicable;
- keep the PRD and policy decision log out of sight unless the participant asks;
- do not explain terms before the participant attempts the task;
- record where the participant hesitates, not only what they say.

Synthetic scenario:

> Students in several Grade 10 classes report that major assignments are often due within the same three-day period. You are not sure whether this is widespread, what causes it, or whether a scheduling change would help.

## 2. Opening script

> We are testing the design, not your ability. Please think aloud and use the synthetic scenario. If something is unclear, tell me what you expected to happen instead of asking me to explain it. I may stay quiet for a moment so I can see what you do naturally.

## 3. Five tasks

### Task 1 — Submit a measurable problem

**Role:** student contributor  
**Screen:** Student problem flow

> You notice the assignment deadline pattern described in the scenario. Show me how you would submit it so another student could understand the problem and the school could investigate it.

Observe:

- whether the participant finds the problem form;
- what they enter as scope, affected group, category, and evidence;
- whether public, anonymous-public, and private-review visibility are understood;
- whether AI clarification is treated as editable assistance;
- whether they notice what happens after submission.

Success signal: participant submits or describes a complete report without moderator coaching and can explain who can see it.

### Task 2 — Turn a cluster into a research question

**Role:** student project leader  
**Screen:** Research workspace

> The report has been grouped with similar reports and validated. Create a research plan that would help the team understand the pattern without claiming that it causes lower grades.

Observe:

- whether “research question,” “population,” “method,” and “limitations” are findable;
- whether methodology warnings are understandable and actionable;
- whether the participant knows a mentor review is required;
- whether they avoid unsupported causal wording.

Success signal: participant produces a descriptive or comparative question and identifies at least one limitation.

### Task 3 — Explain the baseline gate

**Role:** student project leader or mentor  
**Screen:** Impact workspace

> Your team wants to try a shared assessment calendar. Show me what must be defined before the intervention can become active, and explain what the baseline is.

Observe:

- whether primary metric and baseline are visible;
- whether the participant understands the block as a safeguard rather than a technical error;
- whether the theory of change connects action to measurement;
- whether negative or inconclusive results appear acceptable.

Success signal: participant states that baseline is measured before action and can identify the primary metric and owner.

### Task 4 — Find what needs mentor attention

**Role:** mentor  
**Screen:** Mentor review queue

> You have several active teams and only a short time today. Find the work that needs your judgment first, decide what you would review, and tell me what you would expect to happen after requesting changes.

Observe:

- whether the queue prioritizes exceptions rather than every item;
- whether stale, privacy, baseline, and methodology issues are distinguishable;
- whether the participant can find decision history and comments;
- whether the wording feels supportive and actionable.

Success signal: participant identifies a priority item and describes the next state transition.

### Task 5 — Route a sensitive report and review a duplicate

**Role:** moderator/admin  
**Screen:** Moderation queue

> A report contains a personal accusation and another report looks similar to an existing cluster. Show me how you would handle both while protecting the author and preserving the audit trail.

Observe:

- whether private routing is obvious;
- whether the participant understands that AI flags but does not decide;
- whether merge/unmerge controls are separated from suggestion evidence;
- whether the urgent-help route and access information are findable;
- whether the reason, actor, and time are captured.

Success signal: participant routes the sensitive report privately and makes a deliberate, reversible merge decision.

## 4. Debrief questions

Ask after all tasks:

1. What did you think ImpactOS was for?
2. Which part felt most valuable?
3. Which part felt like extra work or school bureaucracy?
4. What would you call a “problem cluster” instead?
5. What does “impact” mean to you here?
6. What would you expect the school to do after a validated problem is published?
7. Which information should never be visible to other students?
8. What would make you trust the privacy message?
9. If you could remove one screen or required field, which one?
10. What is one thing the prototype must do before you would use it in a real project?

## 5. Observation scorecard

Score each task from 1 to 3:

| Score | Meaning |
|---:|---|
| 1 | Could not complete or misunderstood the core concept |
| 2 | Completed with hesitation, workaround, or minor coaching |
| 3 | Completed independently and explained the reason |

Record the first point of friction, not just the final score.

```text
Participant / role:
Task 1 score:   First friction:
Task 2 score:   First friction:
Task 3 score:   First friction:
Task 4 score:   First friction:
Task 5 score:   First friction:

Misunderstood term:
Unexpected permission expectation:
Safety concern:
Missing information:
Suggested change:
Evidence / quote:
```

## 6. Decision rule after testing

Change a wireframe or term when:

- two or more participants make the same wrong assumption;
- one participant identifies a safety or privacy risk;
- a role owner says the screen grants authority they do not actually have;
- a required field cannot be completed with realistic pilot information;
- the participant cannot explain what happens next after a successful action.

Do not add a feature merely because one participant asks for it. Add it to the decision log and test whether it is necessary for the pilot boundary.
