# Cloudscape frontend completion checklist

## Product flow

- The page has one identifiable primary user goal.
- Primary and secondary actions have clear labels and placement.
- Cancel, back, success, deletion, and not-found navigation are defined.
- Destructive and high-impact actions explain consequences.
- Long-running operations communicate progress or pending state.

## States

- Initial loading does not display a false empty state.
- Background refresh does not unnecessarily erase usable data.
- Empty resource state and filtered-no-results state are different.
- Recoverable errors preserve user work.
- Field and page-level errors are mapped correctly.
- Permission-denied and disabled-action behavior are intentional.
- Partial failures are represented when possible.
- Duplicate submission is prevented.

## Cloudscape conformance

- The page uses an appropriate Cloudscape pattern, not merely Cloudscape-looking controls.
- Application shell and page geometry are consistent with neighboring pages.
- Official components are used before custom equivalents.
- Global styles are imported exactly once.
- Spacing and typography use Cloudscape primitives or tokens.
- Custom CSS is local, shallow, minimal, and does not target internal generated classes.
- There is no copied AWS Console private styling or invented Cloudscape API.

## Accessibility

- Every control has an accessible name.
- Form labels, descriptions, constraints, and errors are associated correctly.
- Keyboard users can reach and operate all controls.
- Focus moves predictably for modal, drawer, error, and navigation transitions.
- Status is not communicated by color alone.
- Icon-only actions have meaningful accessible labels.
- Heading hierarchy is logical.
- Dynamic feedback is announced through the component's intended mechanism or existing app infrastructure.

## Responsive behavior

- Narrow screens do not require unintended horizontal page scrolling.
- Tables use appropriate responsive behavior or a justified alternative.
- Action groups remain understandable when space is constrained.
- Long identifiers, labels, and error text wrap or truncate intentionally.
- Drawers, modals, and forms remain usable at small viewport sizes.

## Architecture and correctness

- Existing repository conventions are followed.
- Server, URL, form, transient UI, and capability state are not conflated.
- Request races and stale responses are handled.
- API types are explicit and unsafe casts are minimized.
- Frontend permission checks are not presented as security enforcement.
- New abstractions solve a demonstrated repeated problem.
- No unrelated refactor or dependency was introduced.

## Validation

Run the repository's applicable commands, commonly:

```text
install or lockfile-consistent dependency command
typecheck
unit/integration tests
lint
production build
end-to-end tests when available and relevant
```

Report exact commands and whether they passed. When a command cannot run, explain the concrete reason and provide the remaining manual validation steps.
