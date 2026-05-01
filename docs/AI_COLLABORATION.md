# AI Collaboration Narrative

## Prompt Used

> Help me design a simple systems-engineering final project that demonstrates
> Git workflow, AI code review, tests, CI, and a 10-minute presentation. I want
> the project to be easy and useful, such as checking whether graphs meet ADA
> and inclusivity requirements for color and font choices.

## What ChatGPT Helped With

- Framed the graph-accessibility checker as a systems engineering verification problem.
- Suggested measurable requirements for contrast, font size, labels, and alt text.
- Helped identify edge cases: invalid hex colors, missing axis labels, low-contrast palettes, and too-short alt text.
- Helped plan the Git history so it demonstrates branching, merging, conflict resolution, and CI.

## What I Accepted

- I accepted the idea of using JSON chart metadata instead of image processing because it keeps the project simple and easy to run.
- I accepted using standard-library `unittest` so a fresh clone can run tests without dependency setup.
- I accepted raising clear failures for inaccessible examples because it makes the demo more understandable.

## What I Rejected

- I rejected a heavier computer-vision approach because it would depend on image parsing and external libraries, which would make the demo fragile.
- I rejected vague "AI accessibility score" language because the project should show concrete requirements, not a black-box judgment.

## Reflection

AI was most helpful as a planning and review partner. It helped translate a broad accessibility idea into testable requirements and a small code structure that could be defended in a final presentation. It was least helpful when it suggested larger features than the project needed. The main risk is accepting a polished suggestion without checking whether it actually matches the stakeholder need. My team AI playbook would allow AI to draft prompts, tests, and review comments, but every requirement and merge decision would need a human explanation.
