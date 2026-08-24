# Learner model

`LEARNER.md` is a current, revisable hypothesis. It records observable
capabilities, not broad topic labels.

## States

- `unknown`: no usable evidence.
- `introduced`: explained or encountered, not yet demonstrated.
- `fragile`: understanding or performance is incomplete, inconsistent, or
  dependent on substantial help.
- `supported`: the mental model or procedure is correct, but complete execution
  still depends on references, examples, or assistance.
- `operational`: the mission-relevant task is completed autonomously.
- `retained`: the capability is demonstrated later or transferred to a new
  context.

State is mission-relative. `Operational` never means universal mastery.

## Evidence record

For every state above `unknown`, record:

- observable capability;
- current state;
- result and reasoning;
- assistance: `none`, `light`, `substantial`;
- learner confidence: `low`, `medium`, `high`;
- source record or lesson ID;
- observed date or session;
- misconception or error category;
- next check.

Keep dimensions separate when performance differs. For example, explaining an
algorithm can be `operational` while implementing it is `fragile`; a broad
aggregate may be `supported` but must not erase those dimensions.

## Updating state

States can move backward. Preserve the evidence history and explain the newest
interpretation. Prefer newer independent evidence over immediate guided
performance. Allow the learner to contest the model; record the disagreement
and test it rather than silently accepting or rejecting it.

Use error categories only when they change the next action: missing prerequisite,
term not understood, incorrect mental model, procedure error, transfer failure,
excessive cognitive load, or ambiguous task.

