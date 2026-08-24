# Lesson protocol

Use this protocol for the first `not_done` lesson in the current milestone.

## Unit of teaching

A lesson builds one observable capability tied to the mission and located in
the learner's proximal development zone. It ends only after the learner produces
evidence for that capability. A session may contain more than one lesson, but
each lesson has its own stable ID, source Markdown, evidence record, and PDF.

## Completion criterion

A lesson is complete when its load-bearing prerequisites are available, its
theory and worked examples are source-grounded, the live chat loop has produced
learner evidence, the learner model is updated, and the final PDF passes
verification.

## 1. Select the frontier capability

Choose the highest-value `not_done` capability whose prerequisites are ready and
which fits the remaining milestone time. A `supported` prerequisite is enough
for ordinary continuation; a load-bearing prerequisite must be `operational`.

## 2. Author the lesson source

Read `source-policy.md`, the domain guide, and `pdf-protocol.md`. Create
`.adaptive-teach/lessons/<lesson-id>-<slug>.md` from the lesson template. Ground
every term that the learner must use in the lesson. Include motivation, theory,
worked examples, boundaries or counterexamples, likely misconceptions, sources,
and practice prompts. Keep `status: not_done`.

## 3. Teach in chat

Use the PDF/source as the durable textbook and chat as the live teacher:

1. retrieval from prior material when applicable;
2. concise explanation;
3. explicit pause for questions;
4. worked example;
5. learner attempt;
6. immediate feedback.

Treat interruptions as diagnostic evidence. Offer clarification, another
representation, a counterexample, or an attempt without hints. Do not interpret
an immediate correct answer as retention.

## 4. Record evidence and decide

Create `.adaptive-teach/evidence/<lesson-id>.md`. Record the result, reasoning,
assistance, confidence, misconception taxonomy, and next check. Update
`LEARNER.md` using `learner-model.md`.

- `unknown`, `introduced`, or `fragile`: vary explanation, reduce difficulty,
  or recover a prerequisite; keep the same lesson `not_done`.
- `supported`: advance when the remaining gap is not load-bearing, and schedule
  an unassisted check.
- `operational`: advance and schedule later retrieval.
- `retained`: advance; preserve the delayed or transfer evidence.

## 5. Finalize

Incorporate durable clarifications from chat into the lesson Markdown. Render and
verify the PDF using `pdf-protocol.md`. Validate the workspace. Change the lesson
source and its roadmap row to `done` as the final operations.

