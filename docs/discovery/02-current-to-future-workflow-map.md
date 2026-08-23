# Pilar Impact Lab — Current-to-Future Workflow Map

**Use:** discovery hypothesis to validate with Pilar. This is not a claim about the school's current process.

## 1. How to use this map

During interviews, replace the “current-state hypothesis” with the actual tool, owner, handoff, and delay. Mark each row as:

- `confirmed` — observed or confirmed by the accountable owner;
- `partial` — some roles or teams do this differently;
- `unknown` — needs follow-up;
- `out of scope` — not part of the V1 pilot.

The future-state column is the proposed ImpactOS behavior from the V1 PRD. Change it when discovery shows the school needs a different workflow.

## 2. End-to-end map

| Stage | Current-state hypothesis to validate | Proposed ImpactOS future state | Primary owner | Evidence of completion |
|---|---|---|---|---|
| Notice | Concern starts in conversation, class, club, form, or group chat | Student captures a structured problem with scope, affected group, category, and visibility | Student | Submitted problem draft |
| Clarify | Someone asks follow-up questions informally, or nobody does | AI suggests up to three clarifying questions; student edits or ignores suggestions | Student | Confirmed problem framing |
| Route | A concern may be forwarded manually; sensitive content may be mixed with ordinary feedback | Sensitivity check routes potential safeguarding or personal reports to private review | Moderator/admin | Private-review decision |
| Find duplicates | Similar concerns are discovered through memory or separate conversations | System suggests up to three compatible problem clusters; moderator decides merge | Moderator | Cluster link or no-match rationale |
| Validate | Importance may be inferred from volume, anecdotes, or authority | Students add structured signals and evidence; reviewer decides whether the cluster is validated | Reviewer | Validation decision and reason |
| Investigate | Research plan, sources, and feedback may live in separate tools | Leader creates a linked research workspace with question, population, method, ethics, and limitations | Project leader | Approved research plan |
| Collect | Survey or observation collection may be ad hoc | Approved survey/evidence workflow stores versions, visibility, access, and basic analysis | Research team | Closed survey/evidence snapshot |
| Propose | Intervention may start before a baseline or success metric is explicit | Approved research converts to an intervention proposal with theory of change and metrics | Project leader | Approved proposal |
| Measure | Results may be described without a pre-intervention comparison | Baseline, during, post, and follow-up observations are recorded with evidence | Project team | Observation records |
| Review | Final reports may be shared through a presentation, document, or meeting | Editable impact report is reviewed by a mentor and uses careful observed-result language | Mentor/reviewer | Approved impact report |
| Respond | School or OSIS response may be difficult to find later | Authorized publisher adds a status update and response history to the cluster/project | OSIS/admin | Visible official response |
| Learn | Lessons may remain with a team | Project retains limitations, negative/inconclusive results, and next action for pilot evaluation | Team + sponsor | Evaluation record |

## 3. Handoff and exception map

| Trigger | Proposed route | Decision authority | Required audit trail |
|---|---|---|---|
| Potentially sensitive report | Private review; show urgent-help notice | Designated moderator/admin | Flag, access, decision, escalation |
| Probable duplicate | Suggestion only; author may acknowledge; moderator merges | Moderator | Candidate, decision, reason, merge/unmerge |
| Insufficient evidence | Remain gathering evidence; request rationale or next evidence | Reviewer | Status, reason, next action |
| Research plan missing required section | Changes requested | Mentor | Version, comment, decision |
| Survey asks for sensitive/identifiable data | Block or route for additional review | Mentor/admin | Warning, acknowledgement, approval |
| Approved survey edited | New version; reapproval if required | Mentor/admin | Version lineage, decision |
| No baseline before intervention | Block activation unless reviewer records exception | Mentor/authorized reviewer | Exception reason, approver |
| Team goes stale | Attention queue and configurable reminder | Mentor | Last activity, reminder, resolution |
| Negative/inconclusive result | Complete report with limitations and next action | Team + reviewer | Result, limitations, review decision |
| AI provider unavailable | Continue manually; store no partial unsupported output | User/system | Failure event without sensitive payload |

## 4. Proposed visibility model to validate

| Record | Student contributor | Project team | Mentor | OSIS | Moderator/admin |
|---|---|---|---|---|---|
| Own draft | Own | If invited | Assigned only | No | If authorized |
| Non-sensitive published cluster | School-allowed summary | Yes | Yes | Aggregate/allowed | Yes |
| Private report | Author and designated staff only | No by default | Only if assigned | No | Designated staff |
| Anonymous survey responses | No identity | Aggregate; raw only if approved | Per assignment | Aggregate only | Authorized governance |
| Research plan | Public summary if allowed | Full | Full review | Allowed summary | Full audit access |
| Impact report | Allowed school view | Full editing | Review | Published/allowed view | Full governance |

These are proposed defaults, not confirmed policy. Discovery must identify where Pilar requires stricter or broader access.

## 5. Current-state interview capture table

Complete one row per workflow stage after interviews.

| Stage | Actual tool/place | Actual actor | Handoff | Typical delay | Workaround | Safety issue | Source/session | Confidence |
|---|---|---|---|---|---|---|---|---|
| Notice |  |  |  |  |  |  |  |  |
| Clarify |  |  |  |  |  |  |  |  |
| Route |  |  |  |  |  |  |  |  |
| Find duplicates |  |  |  |  |  |  |  |  |
| Validate |  |  |  |  |  |  |  |  |
| Investigate |  |  |  |  |  |  |  |  |
| Collect |  |  |  |  |  |  |  |  |
| Propose |  |  |  |  |  |  |  |  |
| Measure |  |  |  |  |  |  |  |  |
| Review |  |  |  |  |  |  |  |  |
| Respond |  |  |  |  |  |  |  |  |
| Learn |  |  |  |  |  |  |  |  |

## 6. Pilot-ready future-state slice

```text
Student notices problem
        |
        v
Structured report + visibility choice
        |
        +--> sensitive? ---- yes ---> private review + safeguarding route
        |
        no
        v
Moderator review + duplicate suggestions
        |
        v
Published cluster + structured signals + evidence
        |
        +--> not enough evidence ---> gathering evidence
        |
        validated
        v
Research plan --> mentor review --> approved study --> survey/evidence
        |
        v
Findings + limitations --> intervention proposal + metric + baseline
        |
        +--> missing metric/baseline ---> approval blocked or documented exception
        |
        approved
        v
Active intervention --> observations --> impact review
        |
        v
Published result + official response + next action
```

## 7. Decisions that can invalidate the map

Prioritize these questions before engineering:

1. Does Pilar already have a mandatory concern-reporting channel that ImpactOS must link to or avoid duplicating?
2. Who has authority to validate a problem, approve a survey, and publish an official response?
3. Does “OSIS reviewer” represent one role or multiple people with different access?
4. What is the minimum review required before a student can invite participants or collect responses?
5. Are baseline measurements feasible for the candidate pilot problems?
6. What is the approved route for sensitive or urgent content?
7. Does the school require Bahasa Indonesia, English, or bilingual interface copy?

Until these are answered, keep the prototype data synthetic and keep policy-sensitive screens clearly labeled as “to be configured.”
