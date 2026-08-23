# ImpactOS V1 — Low-Fidelity Wireframe Specification

**Prototype file:** `impactos-wireframes.html`  
**Purpose:** validate workflow, vocabulary, visibility, decision points, and exception handling before visual design or serious development.

## 1. Shared shell

Every authenticated screen uses the same low-complexity shell:

```text
+--------------------------------------------------------------------------------+
| Pilar Impact Lab | [Search]                         [Notifications] [Profile]  |
+------------------+-------------------------------------------------------------+
| Home             |                                                             |
| Problems         |                                                             |
| Research         |                 page content                              |
| Impact projects  |                                                             |
| My tasks         |                                                             |
| Review (role)    |                                                             |
+------------------+-------------------------------------------------------------+
```

Rules:

- The active role and school scope are visible.
- A status badge always has text, not color alone.
- Sensitive/private states use an explicit lock label and a short explanation.
- Every AI suggestion includes “suggestion,” a reason, and an edit/dismiss action.
- Every review action explains what changes next and records the actor, time, and reason.

## 2. Screen inventory

| ID | Screen | Primary user | Critical decision |
|---|---|---|---|
| WF-01 | Student problem flow | Student contributor | Submit a useful, safely visible problem |
| WF-02 | Research workspace | Student leader, mentor | Decide whether the plan is clear, ethical, and measurable |
| WF-03 | Impact workspace | Project team, mentor | Define a baseline and track observed results |
| WF-04 | Mentor review queue | Mentor | Spend attention on the highest-risk or most-stalled work |
| WF-05 | Moderation queue | Moderator/admin | Route sensitive content and make reversible cluster decisions |

## 3. WF-01 — Student problem flow

```text
+--------------------------------------------------------------------------------+
| New problem                                             Step 1 2 3 4            |
| Tell us what is happening, not only what solution you want.                    |
+--------------------------------------------------------------------------------+
| Title                                                                         |
| [ Major assignments are due in the same three-day period                    ] |
|                                                                              |
| What is happening?                                                            |
| [ Describe the pattern, where it occurs, and how often.                    ] |
| [                                                                            ] |
|                                                                              |
| Who is affected? [ Grade 10 students v ]  Scope [ Several classes v ]         |
| Category [ Learning & workload v ]                                            |
|                                                                              |
| Visibility                                                                    |
| ( ) School-visible under my name  ( ) School-visible anonymously              |
| ( ) Private review only             [Why?]                                    |
|                                                                              |
| Evidence (optional now)                                                       |
| [ Upload file ]  [ Add observation ]                                         |
|                                                                              |
| AI framing suggestion — clearly labeled                                      |
| “Could this be about the timing of major assignments?”                       |
| [ Use as a draft ] [ Edit ] [ Dismiss ]                                      |
|                                                                              |
| [Save draft]                                      [Continue to review]         |
+--------------------------------------------------------------------------------+
```

Acceptance questions:

- Can a student tell the difference between public, anonymous-public, and private review?
- Does the form encourage a measurable observation rather than a solution pitch?
- Does the AI card make clear that the student remains the author and decision-maker?
- Is the next step visible after submission?

## 4. WF-02 — Research workspace

```text
+--------------------------------------------------------------------------------+
| Research: Assessment deadline concentration       DRAFT       [Ask mentor]   |
| Problem link: Assessment Workload Concentration     Mentor: Ms. Rani           |
+----------------------+---------------------------------------------------------+
| Overview              | Research question                                    |
| Research plan         | [ How concentrated are major assignment deadlines  ] |
| Evidence & claims     | [ across Grade 10 classes during a typical month? ] |
| Survey                |                                                         |
| Findings              | Question type: [descriptive]  [Use suggestion]       |
| Review history        |                                                         |
|                      | Plan checklist                                      |
|                      | [x] Population  [x] Variables  [ ] Sampling        |
|                      | [ ] Ethics      [ ] Limitations                     |
|                      |                                                         |
|                      | Methodology warnings (2)                            |
|                      | ! Convenience sample may not represent all Grade 10 |
|                      |   Suggested correction: state the sample boundary.  |
|                      | ! “Stress and grades” has two outcomes              |
|                      |   Suggested correction: split into two questions.  |
|                      |                                                         |
|                      | [Save draft] [Submit for mentor review]             |
+--------------------------------------------------------------------------------+
```

Acceptance questions:

- Does the participant understand which checklist items block review?
- Are warnings explanatory and correctable rather than punitive?
- Can the team see the linked problem and evidence without leaving the workspace?
- Is “descriptive” understandable to a high-school student?

## 5. WF-03 — Impact workspace

```text
+--------------------------------------------------------------------------------+
| Impact project: Shared assessment calendar       REVIEW       [Request help]   |
| Linked problem > research > evidence trail                                     |
+--------------------------------------------------------------------------------+
| Theory of change                                                               |
| If teachers coordinate major deadlines in one shared view, then deadline      |
| concentration may decrease for Grade 10 classes, because conflicts are visible.|
|                                                                              |
| Primary metric — required before activation                                   |
| [ Number of major deadlines per three-day window ] [unit: count]              |
|                                                                              |
| Baseline — required before activation                                         |
| [Baseline not recorded]  Before action: [date range] [Add observation]        |
| [!] This project cannot become ACTIVE until a baseline plan is saved.         |
|                                                                              |
| Progress                                                                       |
| [Done] Define calendar  [In progress] Teacher test  [Next] Post measurement   |
|                                                                              |
| Observations                                                                  |
| Baseline  8 windows / 14 deadlines   During  —   Post  —   Follow-up  —       |
|                                                                              |
| Result language                                                               |
| “The post-intervention period showed an observed change of …”                 |
| [Edit impact report] [Submit for impact review]                               |
+--------------------------------------------------------------------------------+
```

Acceptance questions:

- Does the baseline gate make sense before the action starts?
- Can a student distinguish a metric from a goal or a task?
- Does the result wording avoid promising causation?
- Can the team honestly complete the report when the result is negative or inconclusive?

## 6. WF-04 — Mentor review queue

```text
+--------------------------------------------------------------------------------+
| Mentor review queue                     [All] [Due soon] [Stale] [Privacy]    |
| Review the exceptions first; open any item for context and history.             |
+--------------------------------------------------------------------------------+
| NEEDS ATTENTION                                                             4  |
| [HIGH] Survey: deadline pattern             Privacy warning                     |
| Owner: Grade 10 team   Last activity: today   [Open review] [Assign]           |
|                                                                              |
| [HIGH] Impact: shared calendar               Baseline missing                   |
| Owner: Aisha   Due: tomorrow                 [Open project] [Comment]           |
|                                                                              |
| [MED] Research: canteen queue                Changes requested 2 days ago       |
| Owner: OSIS team                            [Open plan] [Send reminder]        |
|                                                                              |
| [LOW] Impact: quiet study space              Stale for 7 days                   |
| Owner: Daniel                              [Open project] [Snooze]             |
+--------------------------------------------------------------------------------+
| REVIEW HISTORY                                                               |
| 23 Aug  Approved research plan — Assessment deadline concentration            |
| 22 Aug  Requested changes — Canteen queue survey                              |
+--------------------------------------------------------------------------------+
```

Acceptance questions:

- Is the queue actionable without reading every project?
- Can a mentor tell why the item is urgent and what decision is needed?
- Are “request changes,” “comment,” “approve,” and “snooze” distinct?
- Is review history sufficient to avoid repeating feedback?

## 7. WF-05 — Moderation queue

```text
+--------------------------------------------------------------------------------+
| Moderation queue                 [Private review] [Duplicates] [Archived]     |
| AI flags content; a designated person decides and records the reason.         |
+--------------------------------------------------------------------------------+
| PRIVATE REVIEW — restricted                                             2    |
| Personal accusation / possible safeguarding issue                            |
| Report: “…”   Submitted: 23 Aug   Visibility: PRIVATE_REVIEW                  |
| Urgent-help route: [school-configured contact / notice]                       |
| [Open restricted record] [Route to safeguarding] [Record decision]             |
|                                                                              |
| DUPLICATE SUGGESTION                                                          |
| New report: Assignment deadlines overlap                                      |
| Candidate cluster: Assessment Workload Concentration   Similarity: suggestion |
| Why shown: similar timing, grade, and category                               |
| [Open both records] [Merge into cluster] [Not a match]                        |
|                                                                              |
| Decision reason (required)                                                    |
| [ Explain the routing or merge decision                                     ] |
| [Save decision + audit event]                                                 |
+--------------------------------------------------------------------------------+
```

Acceptance questions:

- Is the restricted path visually and verbally unmistakable?
- Does the moderator understand that similarity is not a merge decision?
- Is the urgent-help route configurable rather than hard-coded?
- Does every consequential action require a reason?

## 8. Prototype conventions

- Use synthetic names and synthetic records only.
- Show loading and failure states for AI suggestions without blocking manual completion.
- Test with keyboard navigation and a narrow viewport before visual refinement.
- Keep empty states specific: explain what can be done next.
- Do not show likes, public rankings, badges, or popularity counts.
- Keep “official response” separate from student comments or discussion.
