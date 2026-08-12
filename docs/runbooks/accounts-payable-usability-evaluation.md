# Accounts-Payable Usability Evaluation Runbook

**Purpose:** Establish observed reviewer comprehension, correctness, handling-time, and confidence baselines for the invoice exception workflow.

**Product surface:** IntelliPay review queue and invoice detail

**Related criteria:** [Human evaluation](../analysis/evaluation-approach.md#human-evaluation)

## Goal

Determine whether an accounts-payable reviewer can independently understand the invoice, connect material values to source evidence, explain why policy routed the case, and choose a safe next action with an auditable rationale.

## Value

- Reveals comprehension and workflow failures that automated tests cannot observe.
- Measures whether evidence and policy explanations support real decisions.
- Detects unsafe action affordances before operational use.
- Establishes handling-time and confidence baselines for later comparison.
- Turns observed friction into owned product changes or accepted limitations.

## Simulation Status

**Complete on 2026-08-12.** A scripted tabletop exercise plus one live browser walkthrough is recorded in [Accounts-payable usability simulation](accounts-payable-usability-simulation.md). This closes the rehearsal only; representative AP participant evidence remains distinct from simulated evidence.

## Completion Standard

This workstream is complete when:

- Representative AP participants complete the required task set without consulting raw logs.
- Participants answer all four evaluation questions correctly for the cases they complete.
- Every action records the correct actor and a meaningful rationale.
- No participant can execute a disallowed action.
- Refresh and repeated submission create no duplicate decision or payment.
- No blocking comprehension or action defect remains unresolved.
- Handling time, confidence, help requests, and errors are reported as observed baselines.

Do not invent improvement targets before customer or operational baseline data exists.

## Roles

| Role | Responsibility |
|---|---|
| Session facilitator | Introduces tasks, avoids coaching, records observations, and protects participant data |
| Accounts-payable participant | Completes realistic review tasks and explains decisions |
| Note taker | Records timestamps, errors, help requests, quotations, and confidence |
| Product or engineering observer | Watches silently and classifies product findings after the session |
| Finance or AP owner | Confirms task answers and accepts or rejects residual limitations |

Use 3–5 participants for the initial baseline when practical. Include at least one experienced exception handler and one participant unfamiliar with IntelliPay.

## Required Task Coverage

The combined session set must include:

| Scenario | Required behavior |
|---|---|
| Clean invoice | Explain extracted facts and why no exception exists |
| Inventory mismatch | Identify source quantity, available inventory, route, and blocked approval |
| Ambiguous extraction | Inspect extraction assurance, repaired values, and reasoning evidence |
| Revision or duplicate | Explain document relationship and why a second payment is blocked |
| High-value case | Identify amount policy and available human action |
| Prohibited approval | Recognize the disabled action and explain the non-overridable control |

Use synthetic or supplied test data only. Do not expose production invoices, credentials, or personal data during prototype sessions.

## Environment Preparation

1. Install and verify the locked environment:

   ```bash
   uv sync --all-groups
   uv run pytest -q
   ```

2. Use a fresh SQLite database for each participant or reset it to a known snapshot.
3. Process the selected fixtures into that database.
4. Configure a participant-specific prototype identity:

   ```bash
   export INTELLIPAY_DATABASE_PATH=/tmp/intellipay-usability-participant.db
   export INTELLIPAY_REVIEWER_USERNAME=participant-id
   export INTELLIPAY_REVIEWER_PASSWORD='temporary-local-password'
   uv run intellipay-review --host 127.0.0.1 --port 8000
   ```

5. Confirm the queue, detail, source view, and completed history load before the session.
6. Confirm expected answers with the AP or finance owner before testing participants.
7. Prepare a stopwatch or timestamp log and one session record per participant.

## Participant Briefing

Read the following neutral briefing:

> You are reviewing invoice exceptions in IntelliPay. Work as you normally would and think aloud. Use the information available in the application, but do not inspect application logs or source code. I may ask what you understand, but I will not tell you which action to choose. Some actions may be unavailable because of policy.

Tell participants:

- The system uses prototype data and does not move real money.
- Their interface behavior and comments will be recorded as evaluation evidence.
- They may stop or ask a clarifying question at any time.
- The interface is being evaluated, not the participant.

## Per-Task Procedure

For each task:

1. Record the start time when the case is presented.
2. Ask the participant to open the case from the queue.
3. Allow silent inspection and think-aloud commentary without coaching.
4. Ask the four required questions:
   1. What did IntelliPay extract?
   2. Which source evidence supports each material value?
   3. Which findings and policy rules caused the route?
   4. What action is available, and what will happen after it is selected?
5. Ask the participant to select the appropriate action and enter a rationale.
6. Record completion time when the completed state is visible.
7. On one designated task, refresh the completed page and repeat the same submission attempt. Confirm no duplicate decision or payment appears.
8. Ask for confidence on a 1–5 scale:
   - 1: not confident
   - 2: slightly confident
   - 3: moderately confident
   - 4: confident
   - 5: very confident
9. Record any help request, hesitation, incorrect action, unavailable-action attempt, or misleading interpretation.

## Scoring Rules

### Task Completion

- `PASS`: Correct action and meaningful rationale without facilitator guidance.
- `PASS_WITH_HELP`: Correct completion after procedural help that did not reveal the answer.
- `FAIL`: Incorrect action, unsafe interpretation, abandonment, or answer supplied by the facilitator.

### Four-Question Correctness

Score each question independently:

- `CORRECT`: Material facts and consequences are accurate.
- `PARTIAL`: Main conclusion is correct but material evidence or policy is omitted.
- `INCORRECT`: Material fact, route, action, or consequence is wrong.

The usability gate requires correct answers, not merely successful button clicks.

### Finding Severity

| Severity | Definition | Required response |
|---|---|---|
| Blocking | Prevents completion or causes an unsafe decision | Fix and rerun the affected task |
| Major | Requires help or causes material misunderstanding | Fix or obtain explicit owner acceptance before closure |
| Minor | Creates friction without changing the decision | Track with owner and priority |
| Enhancement | Useful improvement outside the current gate | Add to backlog with rationale |

Classify root cause as `UX`, `POLICY`, `DATA`, `MODEL`, `WORKFLOW`, or `TRAINING`.

## Session Controls

- Do not coach participants toward a route or action.
- Do not count time spent on facilitator interruptions as active handling time.
- Do not change task wording between participants unless the change is recorded.
- Do not reuse a completed mutable database state for another participant.
- Do not treat a disabled button as sufficient authorization enforcement; verify the server rejects the action.
- Do not record passwords, API keys, or unnecessary participant personal information.

## Analysis Procedure

1. Aggregate task completion and four-question correctness by scenario.
2. Report median and range for active handling time; small prototype samples do not justify precise population claims.
3. Report the distribution of confidence scores rather than only an average.
4. Count help requests, incorrect actions, prohibited-action attempts, and duplicate side effects.
5. Group qualitative findings by severity and root cause.
6. Convert every blocking or major finding into a tracked product change or an explicitly accepted limitation with owner and rationale.
7. Rerun affected tasks after fixes. Keep original and follow-up results distinct.

## Final Gate

- [ ] Required scenarios were represented across the sessions.
- [ ] Participants worked without raw logs or source code.
- [ ] All four evaluation questions were scored for every completed task.
- [ ] Actions and rationales were persisted under the participant identity.
- [ ] Disallowed actions were not executable.
- [ ] Refresh and resubmission produced zero duplicate decisions and payments.
- [ ] No blocking issue remains open.
- [ ] Major issues are fixed or explicitly accepted by the AP or finance owner.
- [ ] Handling-time and confidence baselines are published without invented improvement claims.
- [ ] The AP or finance owner signs the evaluation summary.

## Session Record Template

Create one copy per participant. Use a non-identifying participant code where possible.

- **Participant code:**
- **AP experience level:**
- **Session date:**
- **Facilitator:**
- **Note taker:**
- **Application version or commit:**
- **Database or fixture set:**

| Task | Scenario | Completion | Q1 | Q2 | Q3 | Q4 | Active time | Help requests | Confidence |
|---|---|---|---|---|---|---|---:|---:|---:|
| 1 |  |  |  |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  |  |  |
| 4 |  |  |  |  |  |  |  |  |  |
| 5 |  |  |  |  |  |  |  |  |  |

### Observations

| Time or task | Observation or quotation | Severity | Root cause | Proposed response |
|---|---|---|---|---|
|  |  |  |  |  |

### Participant Debrief

1. Which information was easiest to trust?
2. Which information was hardest to understand?
3. Did any available or unavailable action surprise you?
4. What additional evidence would you need in daily work?
5. Overall confidence, 1–5:

## Evaluation Summary Template

- **Evaluation dates:**
- **Participant count:**
- **Task count:**
- **Scenarios covered:**

| Measure | Result |
|---|---:|
| Tasks completed |  |
| Tasks completed without help |  |
| Four-question answers correct |  |
| Incorrect actions |  |
| Prohibited actions executed | 0 required |
| Duplicate decisions | 0 required |
| Duplicate payments | 0 required |
| Median active handling time |  |
| Confidence distribution |  |
| Blocking findings open | 0 required |

### Findings and Disposition

| Finding | Severity | Root cause | Owner | Resolution or accepted limitation | Retest result |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

### Sign-Off

- **Decision:** Passed / Passed with accepted limitations / Not passed
- **Accepted limitations:**
- **AP or finance owner:**
- **Decision date:**
- **Approval reference:**
