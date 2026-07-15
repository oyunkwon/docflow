# Frontend architecture and state logic

## Contents

1. Repository-first policy
2. Recommended layers
3. State ownership
4. API and mutation behavior
5. Permissions
6. Routing
7. Mocking and prototypes
8. Implementation sequence

## 1. Repository-first policy

Inspect before adding patterns. Prefer the existing repository's valid conventions over this reference. Do not add Redux, Zustand, TanStack Query, React Hook Form, or another dependency solely from personal preference.

Adopt a new dependency only when:

- the repository has no adequate solution
- the feature has enough complexity to justify it
- the dependency is compatible with the toolchain
- the user accepts the architectural change or the change is clearly within task scope

## 2. Recommended layers

A practical page slice may contain:

- route/page entry
- page-level orchestration component
- presentational sections
- domain types
- service or API adapter
- query/mutation hook when the project uses hooks
- form mapping and validation
- tests

Keep Cloudscape-specific display concerns out of low-level API clients. Convert transport shapes into domain/view models at a clear boundary when the API shape is awkward or unstable.

Do not create generic wrappers around every Cloudscape component. Wrap only when enforcing real application-wide behavior, such as a standard page shell, permission-aware action, error boundary, or repeated domain form control.

## 3. State ownership

### Server state

Let the existing query/cache layer own request status, cached data, invalidation, and refetch behavior. Without a library, create a small explicit hook or reducer rather than scattering fetch calls across child components.

Prevent stale responses from overwriting newer user intent. Abort obsolete requests where supported or guard by request identity.

### URL state

Store state in the URL when users reasonably expect refresh, back/forward navigation, bookmarking, or sharing to preserve it. Common examples:

- selected resource identifier
- search/filter expression
- sorting
- pagination
- meaningful tab

Parse URL state defensively and normalize invalid values.

### Form state

Keep draft values local to the form or the repository's form library. Derive values rather than duplicating them when possible. Separate client validation from server validation, and clear stale server errors when relevant fields change.

### Transient UI state

Keep modal/drawer visibility, local disclosure, and short-lived selection near the owning component. Lift state only when multiple siblings coordinate around it.

## 4. API and mutation behavior

Define an API contract before wiring controls. For each operation specify:

- request type
- response type
- validation error shape
- general error shape
- idempotency or duplicate-submit behavior
- cache invalidation or refresh behavior
- partial failure semantics

For mutations:

1. Disable or guard duplicate submission.
2. Preserve user input during recoverable errors.
3. Map field errors to fields.
4. Show page-level errors for operation failures.
5. Update or invalidate affected data.
6. Move focus or announce feedback appropriately.
7. Avoid optimistic updates for high-risk operations unless rollback behavior is reliable.

## 5. Permissions

Model permissions as capabilities such as `canCreate`, `canEdit`, and `canDelete`, not scattered role-name comparisons. The frontend may consume capabilities from session or resource data.

Use capability state for presentation only. Never claim it enforces security. Expect the server to reject unauthorized requests and handle that response gracefully.

## 6. Routing

Use the existing router. Give list, detail, create, and edit pages stable routes when they are substantial tasks.

A conventional route family may be:

```text
/resources
/resources/new
/resources/:resourceId
/resources/:resourceId/edit
```

Do not force this shape when the repository has another established convention. Define post-create, post-delete, cancel, and not-found navigation explicitly.

## 7. Mocking and prototypes

When no API exists:

- define realistic TypeScript types
- create a service interface matching the expected asynchronous behavior
- simulate loading and at least one error path
- use deterministic sample data
- isolate mocks so they can be replaced without rewriting the page
- state which contract details are assumptions

Do not embed large mock arrays directly inside the primary page component.

## 8. Implementation sequence

Prefer a vertical slice:

1. route and application shell
2. typed service boundary
3. main happy path
4. loading and empty states
5. errors and permissions
6. secondary actions and overlays
7. responsiveness and accessibility
8. tests and cleanup

Avoid building a speculative component framework before one complete user flow works.
