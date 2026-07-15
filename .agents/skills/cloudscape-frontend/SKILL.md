---
name: cloudscape-frontend
description: Build, extend, review, or migrate React and TypeScript frontends that use the Cloudscape Design System. Use for Cloudscape page creation, enterprise admin consoles, dashboards, resource lists and details, forms, wizards, settings, navigation shells, loading/error/empty states, accessibility reviews, responsive behavior, API-facing UI state, test planning, and conversion of custom or other-library UI into Cloudscape. Support both greenfield prototypes and edits to existing repositories; preserve existing architecture unless the user explicitly requests a migration.
---

# Cloudscape Frontend

Create production-oriented Cloudscape interfaces from product requirements or existing code. Treat Cloudscape as a UX system with page patterns, state conventions, accessibility rules, and responsive behavior—not merely a component library.

## Operating principles

1. Understand the user task before selecting components.
2. Prefer an official Cloudscape component or pattern over custom markup.
3. Preserve an existing repository's routing, data-fetching, state-management, naming, linting, and testing conventions unless they are clearly broken or the user requests a migration.
4. Keep server state, form state, URL state, and transient UI state conceptually separate.
5. Implement every meaningful asynchronous state: initial loading, background refresh, empty result, filtered-no-result, recoverable error, destructive-action failure, partial failure, and success feedback.
6. Use Cloudscape tokens and layout primitives. Avoid arbitrary CSS, copied AWS Console styling, deep selectors into component internals, and visual overrides that fight the design system.
7. Do not invent Cloudscape props or APIs. When uncertain or when version sensitivity matters, check the current official Cloudscape documentation or installed package types.
8. Keep accessibility behavior intact. Do not replace semantic Cloudscape controls with clickable `div` elements or inaccessible custom interactions.
9. Produce code that is runnable in the user's project, not isolated pseudo-code, unless the user explicitly asks for a concept sketch.

## Scope boundaries

Cover:

- React and TypeScript application UI
- Vite, Next.js client applications, or an existing React toolchain
- Application shells and navigation
- Resource list, detail, create, edit, delete, settings, dashboard, and workflow pages
- Tables, cards, forms, filters, pagination, selection, modals, drawers, flash messages, and help panels
- API-facing types, adapters, query hooks, mock services, and UI-side authorization behavior
- Responsive design, internationalization-aware layout, keyboard behavior, and accessibility
- Unit, integration, and end-to-end test plans or tests when the repository supports them
- Cloudscape migration and design-system conformance review

Do not take ownership of:

- Backend business logic, database schema, authentication server, infrastructure, or deployment
- Security policy definition or authorization enforcement on the server
- Brand redesign that requires forking or visually replacing Cloudscape
- Figma asset production unless separately requested

You may define API contracts, mock responses, route guards, capability checks, and frontend integration seams necessary to implement the UI. Clearly mark assumptions that require backend confirmation.

## Workflow decision tree

Determine the task type first:

- **New application or page**: follow the creation workflow.
- **Feature inside an existing repository**: follow the repository-edit workflow.
- **Migration from custom UI or another component library**: follow the migration workflow.
- **Review, bug fix, or accessibility audit**: follow the review workflow.
- **Ambiguous product idea**: infer a sensible enterprise-console flow, state assumptions briefly, and build the smallest coherent vertical slice. Do not block on non-critical questions.

For component and pattern choices, read `references/cloudscape-patterns.md`.
For architecture and state decisions, read `references/frontend-architecture.md`.
For validation before completion, read `references/quality-checklist.md`.

## Creation workflow

1. Translate the request into user goals, primary entities, main actions, permissions, and failure cases.
2. Define the page family:
   - application shell
   - resource collection
   - resource detail
   - create/edit form
   - multi-step workflow
   - dashboard/overview
   - settings/configuration
3. Draft the information architecture and route map before writing components.
4. Choose the Cloudscape page pattern and components using `references/cloudscape-patterns.md`.
5. Define TypeScript domain types and explicit view states.
6. Define the API boundary. Reuse an existing client; otherwise create a small typed service interface. Use mock data only when no real API is available.
7. Implement the shell and page structure first, then collections/forms, then dialogs and feedback.
8. Add loading, empty, error, permission, validation, optimistic/pessimistic mutation, and success behavior.
9. Add tests consistent with the repository. At minimum, specify critical test cases when code execution or test infrastructure is unavailable.
10. Run available type checks, tests, linting, and builds. Fix failures caused by the change.
11. Review against `references/quality-checklist.md` and summarize changed files, assumptions, and unresolved backend dependencies.

## Repository-edit workflow

1. Inspect the repository before proposing architecture. Find:
   - package manager and scripts
   - installed Cloudscape version
   - routing
   - data-fetching and API clients
   - state management
   - shared page shell and layout wrappers
   - form conventions
   - test setup
   - linting and formatting rules
2. Identify the nearest analogous page or component and reuse its conventions.
3. Make the smallest coherent change. Avoid unrelated rewrites and dependency additions.
4. Extend shared abstractions only when at least two real call sites benefit or the current abstraction blocks correctness.
5. Preserve public component APIs unless changing them is necessary; update all call sites when it is.
6. Validate with the repository's own scripts.
7. Report files changed and any behavior that could not be validated.

## Migration workflow

1. Inventory the current screen by user task, not by source component name.
2. Map structure and behavior to Cloudscape patterns before replacing individual controls.
3. Preserve domain behavior, URLs, analytics hooks, permissions, and test selectors unless the user requests changes.
4. Replace layout and interaction patterns in coherent sections; do not create a visually mixed half-migration without clearly isolating the boundary.
5. Remove obsolete CSS and dependencies only after confirming no remaining usage.
6. Test keyboard navigation, focus movement, overlays, table behavior, responsive layout, and error states after migration.

## Review workflow

Review in this order:

1. User-flow correctness and missing states
2. Incorrect Cloudscape pattern or component selection
3. Accessibility and keyboard behavior
4. State ownership and async race conditions
5. Responsive behavior and content density
6. Type safety and API error handling
7. Unnecessary custom CSS or reinvention
8. Test gaps

Return concrete findings with file locations and actionable fixes. Prioritize defects over cosmetic preferences. When asked to fix issues, implement the fixes rather than only describing them.

## State model

Represent page state explicitly. Distinguish:

- **Server state**: fetched data, cache, freshness, request errors
- **URL state**: selected resource, filters, sorting, pagination, tabs when shareable
- **Form state**: field values, touched state, client validation, server validation
- **Transient UI state**: modal visibility, drawer visibility, local selection, dismissible messages
- **Capability state**: whether an action is visible, disabled, or unavailable

Do not use a single boolean such as `isLoading` to represent mutually different phases. Prefer discriminated unions or a query library's status model when they improve clarity.

Do not rely on frontend checks for security. Frontend capability checks improve usability; the backend must still enforce authorization.

## Cloudscape implementation rules

- Import Cloudscape global styles once at the application entry point.
- Prefer per-component imports from `@cloudscape-design/components/...` following the installed package's supported usage.
- Use `AppLayout` for application-level structure when appropriate.
- Use semantic page headers and a single clear primary action per page or workflow stage.
- Use collection hooks or the repository's existing collection abstraction for filtering, sorting, pagination, and selection; do not hand-roll inconsistent table state without reason.
- Use `Flashbar` or the existing application notification system for operation-level feedback.
- Use `FormField` to connect labels, descriptions, constraints, and errors to controls.
- Confirm destructive actions and explain impact. Disable repeated submissions while a mutation is pending.
- Keep visible labels specific. Avoid generic labels such as “Submit” when “Create environment” or “Save policy” is clearer.
- Use drawers, modals, and separate pages according to task complexity; do not place long multi-section forms in a modal.
- Keep empty states actionable and distinguish an empty resource set from a filtered result with no matches.
- Use Cloudscape spacing and typography rather than arbitrary margins and font sizes.
- Add custom CSS only for domain-specific layout not expressible through Cloudscape primitives. Keep it shallow, local, and token-based.

## Output expectations

When changing files, provide:

1. The implemented code or artifact
2. A concise summary of the chosen page pattern and behavior
3. Files changed
4. Validation performed and results
5. Assumptions or backend contracts still requiring confirmation

When only designing the solution, provide:

1. User flow and route map
2. Page hierarchy
3. Cloudscape component/pattern mapping
4. State and API model
5. Error, empty, loading, and permission behavior
6. Implementation sequence
7. Acceptance criteria

Avoid dumping a long component catalog. Explain choices in terms of the user's task.

## Completion criteria

Do not consider the task complete until:

- The primary user flow works end to end or is fully specified.
- All meaningful states are implemented or documented.
- Components and patterns follow current Cloudscape guidance.
- Keyboard and accessible labeling behavior are preserved.
- The UI is usable at narrow and wide viewport sizes.
- Type checks, tests, lint, and build have been run when available.
- No invented APIs, unexplained placeholders, or silent backend assumptions remain.
