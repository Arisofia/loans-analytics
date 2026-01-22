# PR: Fix TypeScript/ESLint Warnings in Frontend (apps/web)

## Summary
This PR addresses all current TypeScript/ESLint warnings in the frontend codebase (apps/web). The main issues resolved include:
- Replacing or refining all uses of the `any` type (`@typescript-eslint/no-explicit-any`)
- Removing or refactoring forbidden non-null assertions (`@typescript-eslint/no-non-null-assertion`)
- Updating or removing unexpected `console` statements (only `warn` and `error` allowed)

No functional changes are introduced—this is a code quality and maintainability improvement only.

## Checklist
- [ ] All `any` types replaced with more specific types or generics where possible
- [ ] All non-null assertions removed or replaced with safe checks
- [ ] All `console` statements updated to comply with project lint rules
- [ ] Lint passes with zero warnings or errors: `npm run lint` in apps/web
- [ ] All existing tests pass: `npm test` in apps/web
- [ ] No user-facing or functional changes

## Reviewer Guidance
- Focus on type safety improvements and code clarity
- Confirm that all lint warnings are resolved
- Validate that no logic or behavior has changed

## Assignees
<!-- Assign to relevant team members who should review this PR -->

---

_This PR is part of the ongoing code quality initiative. Please review and suggest further improvements as needed._
