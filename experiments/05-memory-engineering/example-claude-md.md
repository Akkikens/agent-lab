# Example CLAUDE.md — Optimized for Token Efficiency

This file shows what a WELL-STRUCTURED CLAUDE.md looks like.
It costs tokens every turn, so every line must earn its place.

---

## The Actual Example (copy this pattern):

```markdown
# MyProject

## Build & Run
- `pnpm dev` — start dev server (port 3000)
- `pnpm test` — run tests (vitest)
- `pnpm test path/to/file` — run single test file
- `pnpm lint` — eslint + prettier check
- `pnpm db:push` — push schema changes to dev DB

## Critical Rules
- Never import from `@internal/` outside the `lib/` directory
- API routes must validate input with zod schemas in `lib/validators/`
- All database queries go through `lib/db/queries/` — no raw SQL in route handlers
- Feature flags: check `lib/flags.ts` before adding conditional logic

## Structure
- `app/` — Next.js pages and API routes
- `lib/` — Shared logic (db, auth, utils, validators)
- `components/` — React components (colocated tests as `.test.tsx`)
```

---

## Analysis: Why This Works

**Total: ~150 tokens.** Loaded every turn.

What's included:
- Build commands (can't derive from package.json without reading it)
- Rules that override normal behavior (the agent would do wrong without these)
- Structure overview (saves a directory listing tool call every time)

What's NOT included:
- Code patterns (derivable from code)
- Git conventions (derivable from git log)
- Testing patterns (derivable from existing tests)
- Architecture details (derivable from reading the code)
- Style guide (derivable from linter config + existing code)

## The Test: "Would Claude Do the Wrong Thing Without This Line?"

For each line in CLAUDE.md, ask:
- If this line wasn't here, would Claude do something incorrect?
- YES → Keep it
- NO → Remove it (Claude can figure it out from the code)

Examples:
- "Use vitest not jest" → KEEP (might guess wrong)
- "Functions use camelCase" → REMOVE (can see from code)
- "Never import from @internal/ outside lib/" → KEEP (non-obvious constraint)
- "Components are in components/" → BORDERLINE (could ls, but saves a tool call)
