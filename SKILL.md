---
name: adaptive-teach
description: Run a persistent, evidence-driven learning course with diagnostic onboarding, adaptive lessons, verified lesson PDFs, and milestone replanning. Use only when the user explicitly wants a multi-session learning project, not for one-off explanations.
---

# Adaptive Teach

Treat the current directory as one learning project. Keep all course state under
`.adaptive-teach/`. The public interface is one explicit skill; load only the
protocol for the current phase.

## Route the current phase

1. If `.adaptive-teach/` is absent, run `scripts/init_workspace.py .` and begin
   onboarding.
2. Read `.adaptive-teach/ONBOARDING.md`, `.adaptive-teach/ROADMAP.md`, and
   `.adaptive-teach/LEARNER.md` at low resolution.
3. Route to exactly one phase:
   - Onboarding is `not_done`: read [references/onboarding-protocol.md](references/onboarding-protocol.md).
   - The current milestone has a `not_done` lesson: read [references/lesson-protocol.md](references/lesson-protocol.md).
   - Every planned lesson in the current milestone is `done`, but the milestone
     is `not_done`: read [references/milestone-protocol.md](references/milestone-protocol.md).
   - The mission is `done`: summarize the evidence and stop.

Resume a `not_done` item by redoing the same item and reusing its ID. Do not
create the next item until the previous one is `done`.

## Invariants

- Write `status: done` as the final operation, after every required artifact and
  evidence check succeeds.
- `ONBOARDING.md` is the historical intake record. `LEARNER.md` is the current
  learner hypothesis. `ROADMAP.md` is the current plan. Markdown lesson sources
  are canonical; PDFs are derived outputs. Chat is interaction, not persistent
  state.
- Ground every load-bearing term and prerequisite in demonstrated learner
  evidence or define it before relying on it.
- Advance ordinary competencies from `supported`; require `operational` for
  load-bearing prerequisites.
- Keep the complete destination visible at low resolution. Detail only the
  current milestone, whose maximum duration is three months.
- Teach in chat and maintain one source Markdown plus one verified PDF per
  lesson. At milestone close, compile one verified PDF per module.
- Present workload as a range with assumptions and confidence. Re-estimate from
  observed effort at module and milestone boundaries.

Read [references/workspace-contract.md](references/workspace-contract.md) before
creating, validating, or changing course files. Read
[references/learner-model.md](references/learner-model.md) whenever recording or
interpreting evidence. Read [references/source-policy.md](references/source-policy.md)
before researching course content. Read [references/pdf-protocol.md](references/pdf-protocol.md)
only when authoring or verifying PDFs.

## Domain routing

Load one domain guide when planning assessment or practice:

- Computing: [references/domains/computing.md](references/domains/computing.md)
- Mathematics or physics: [references/domains/mathematics-physics.md](references/domains/mathematics-physics.md)
- Languages: [references/domains/languages.md](references/domains/languages.md)

The V1 is scoped to learning and practice in these domains. It does not manage
the execution of a broader real-world project.
