---
schema_version: 1
lesson_id: M01-L01
module_id: M01-U01
status: not_done
domain: mathematics-physics
capability: Explain how one bubble-sort pass establishes its suffix invariant
---

# From adjacent swaps to an invariant

## Outcome

Explain why a complete left-to-right pass moves the largest remaining value to
the end of the active range, then connect the reasoning to a physical invariant.

## Why this matters

Code is easier to reconstruct when you understand the claim maintained by each
step. The same habit appears in physics: define what remains true while a system
changes.

> A procedure is operational when you can justify the result, not merely repeat
> its syntax.

## Theory

Compare adjacent values. When the left value is larger, swap the pair. After
processing position `i`, the largest value seen so far occupies position
`i + 1`. Therefore the largest value in the active range reaches its right edge
after a full pass.

For comparison, Newton's second law can be written as `$F = ma$`. Its use also
depends on stated modeling assumptions and units.

한국어 예시: 인접한 두 값을 비교하고 순서가 잘못되면 교환합니다.

## Worked example

| Step | Active values | Established fact |
|---|---|---|
| Start | 3, 1, 2 | No suffix is fixed |
| Compare 3 and 1 | 1, 3, 2 | 3 is the largest seen value |
| Compare 3 and 2 | 1, 2, 3 | 3 is fixed at the right edge |

```python
for index in range(len(values) - 1):
    if values[index] > values[index + 1]:
        values[index], values[index + 1] = values[index + 1], values[index]
```

## Boundary or counterexample

One pass does not sort every input. It establishes only the suffix claim needed
by the next pass.

## Practice

1. Trace one pass over `4, 2, 5, 1`.
2. State the invariant without mentioning Python syntax.
3. Explain why the loop stops before the last index.

## Sources

- Python documentation, language reference for assignment semantics.
- A source-grounded algorithms curriculum should be added before a real lesson
  is marked complete.

