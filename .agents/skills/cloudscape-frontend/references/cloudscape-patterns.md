# Cloudscape pattern selection

## Contents

1. Page-family decision table
2. Application shell
3. Resource collections
4. Resource details
5. Forms and creation flows
6. Overlays and secondary tasks
7. Feedback and exceptional states
8. Component selection anti-patterns

## 1. Page-family decision table

Choose by the user's job:

| User job | Default pattern | Typical Cloudscape building blocks |
|---|---|---|
| Browse and act on many resources | Resource collection | `Table` or `Cards`, collection preferences, filtering, pagination, selection, `Header` |
| Inspect one resource | Resource detail | `ContentLayout`, `Header`, `SpaceBetween`, `Container`, `KeyValuePairs`, tabs where justified |
| Create or edit a simple resource | Form page | `Form`, `FormField`, controls, page-level actions |
| Complete a staged or risky setup | Wizard | `Wizard`, step validation, review step, final result feedback |
| Monitor status and trends | Dashboard/overview | `ContentLayout`, `Grid`, `Container`, status indicators, charts only when they answer a decision question |
| Configure a product or account | Settings | Sectioned form or detail/edit pattern; split independent save domains |
| Perform a short contextual task | Modal or drawer | `Modal` for blocking confirmation/short input; drawer for supporting context or inspect-without-leaving |

Do not choose a component because it is visually attractive. Choose it because its interaction model matches the task.

## 2. Application shell

Use an application shell when the feature belongs to a multi-page console.

Typical structure:

- top navigation if the host application uses it
- `AppLayout`
- side navigation for stable product destinations
- breadcrumbs for hierarchy, not browser history
- main content
- optional tools/help panel
- optional split panel for contextual detail

Keep navigation labels task-oriented and stable. Do not put transient filters or record-specific actions in side navigation.

Use `ContentLayout` when the page has a header and content regions that should align with Cloudscape's page geometry. Use `Box`, `SpaceBetween`, `Grid`, and `Container` for composition before adding custom CSS.

## 3. Resource collections

Use `Table` when comparison across columns matters, row density is useful, or bulk actions exist. Use `Cards` when identity, summary content, or visual grouping matters more than cross-row comparison.

Define:

- stable item identity
- column or card definition
- filtering model
- sorting model
- pagination model
- selection mode
- loading and refresh behavior
- empty resource state
- no-match filtered state
- row-level and bulk actions
- action eligibility for mixed selection

Prefer URL-backed filters, sorting, pagination, and selected tabs when users benefit from refreshable/shareable state. Avoid URL state for transient checkbox selection unless the product requires it.

For large or server-side collections, make filtering, sorting, and pagination explicit API concerns. Do not pretend a client-side collection contains the full dataset.

Bulk actions must define partial eligibility and failure behavior. Never imply atomic success if the backend can partially fail.

## 4. Resource details

A detail page should answer:

- What is this resource?
- What state is it in?
- What can the user do next?
- What important configuration or relationships does it have?
- What recent events or failures require attention?

Place the identity and primary status in the page header. Put the principal action in the header when it applies to the whole resource. Group related facts into containers or key-value groups.

Use tabs only for peer information domains with meaningful content. Do not hide the primary summary or critical warnings behind a tab. Preserve tab selection in the URL when deep-linking matters.

For destructive actions, state impact and dependencies. Redirect predictably after deletion and show operation feedback.

## 5. Forms and creation flows

Use a single form page when the task is understandable at once and fields have one save boundary. Use a wizard when:

- steps depend on earlier choices
- there are multiple conceptual stages
- validation or provisioning is expensive
- a review step materially reduces risk
- users may need guidance through unfamiliar setup

Do not use a wizard merely because a form is long. First reduce, group, and progressively disclose fields.

For each field define:

- label
- optional/required status
- description or constraint text when needed
- initial value
- client validation
- server validation mapping
- disabled/read-only condition
- dependency on other fields
- serialization format

Use page-level error summaries when submission fails for reasons not attributable to a single field. Attach field-specific server errors to their fields when possible.

Keep cancel behavior explicit. Warn before discarding meaningful unsaved changes when the host application's conventions support it.

## 6. Overlays and secondary tasks

Use a modal for short, focused, blocking decisions such as confirmation or a compact form. Avoid multi-section, scroll-heavy workflows in a modal.

Use a drawer or split panel for contextual inspection, supporting information, or secondary editing that benefits from retaining page context.

Use a separate page for complex creation/editing, tasks requiring deep links, or flows with substantial validation and help content.

Manage focus correctly when opening and closing overlays. Provide a clear title, action labels, cancel path, pending state, and error behavior.

## 7. Feedback and exceptional states

### Loading

Use loading indicators that preserve page context. Avoid flashing an empty state before data resolves. For background refresh, keep existing data visible and show a subtle refresh state.

### Empty

Differentiate:

- no resources exist yet
- filters return no matches
- data is unavailable because of permissions
- data failed to load

The first should usually explain the resource and offer a creation action. The second should offer clearing or changing filters.

### Errors

State what failed, what remains safe, and what the user can do. Preserve entered form data after a recoverable failure. Provide retry only when retrying is meaningful.

### Success

Use durable feedback for asynchronous operations whose result is not immediately obvious. Avoid success messages for actions whose visual result is already unmistakable unless the product convention requires them.

### Permissions

Hide actions that are irrelevant and can never be used. Disable actions when showing the reason helps users understand policy or prerequisite state. Use an access-denied state when the entire page is unavailable.

## 8. Component selection anti-patterns

Avoid:

- a table for data that users do not compare
- cards for dense bulk management
- tabs as a substitute for information architecture
- modals for long workflows
- custom dropdowns, toggles, pagination, or notifications when Cloudscape already supplies them
- multiple competing primary buttons
- icon-only controls without accessible names and tooltips where needed
- placeholder text as the only field label
- status represented by color alone
- custom spacing that makes adjacent pages visually inconsistent
