## Why

Learned lines are currently marked only by reducing the whole row's opacity to 0.6. Opacity is a subtractive signal: it needs substantial foreground content to be perceivable. In Listening mode a closed row contains almost nothing — a faint twisty triangle, a play button, and a line number — so fading them further is invisible in practice, and the learner cannot tell at a glance where they left off. A learned row needs an additive signal (a tint) that is perceivable whether or not the row shows text.

## What Changes

- Replace the learned-row styling rule (`.line.learned { opacity: 0.6; }`) with a light gray row background (`.line.learned { background: #f1f1f2; }`).
- Remove the opacity reduction entirely rather than layering it on top of the tint: `opacity` applies to the row's background as well, so keeping it would wash the new gray band back out toward the page background.
- Learned rows remain fully interactive (toggle, play, selection, extraction), and the `.learned` class remains the observable state that both initial render and the live `markLearnedUpTo` update key off. No JS or Python changes are needed.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `practice-dialog`: The "Scroll position restore" requirement changes how a learned line is styled — a light gray row background instead of reduced opacity, with no green or other colored highlight. The interactive and observability guarantees stay as they are.

## Impact

- Affected code: `language_study_anki/practice_dialog.py` — one CSS rule inside the inline `_HTML` template. No JS, bridge, or Python logic changes.
- Affected specs: `openspec/specs/practice-dialog/spec.md` ("Scroll position restore" requirement and its "Learned rows are faded, not green" scenario, once synced).
- Tests: no test asserts the learned-row styling; none require changes.
