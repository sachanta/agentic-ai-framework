# UI Verification — Fix Plan

Source report: Devin UI verification (2026-04-15). Three issues were found; all three are confirmed against the current working tree. Pages render correctly once these are resolved — this plan is about making a fresh clone work out of the box on a supported Node version.

## Summary

| # | Issue | Severity | Blocks fresh clone? | Est. effort |
|---|-------|----------|---------------------|-------------|
| 1 | `frontend/src/lib/utils.ts` untracked in git | **P0** | Yes — app fails to compile | 2 min |
| 2 | MSW handler URL mismatch for login | **P1** | No, but mock login is broken | 5 min |
| 3 | `tailwind.config.js` mixes CommonJS `require()` with ESM | **P1** | Breaks on Node 22+ | 5 min |

Total: ~15 min of edits, plus test & verification.

---

## Issue 1 — `src/lib/utils.ts` not committed

### Evidence

```bash
$ git ls-files frontend/src/lib/utils.ts
(empty — file is not tracked)

$ cat frontend/src/lib/utils.ts
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

The file exists on the current dev box (Devin or an earlier session created it), but a fresh clone won't have it. 22+ shadcn/ui components import `cn` from `@/lib/utils`, so the build breaks immediately.

### Root cause hypothesis

When shadcn/ui components were added, the generator scaffolds `src/lib/utils.ts` alongside. Either:
- The file was in `.gitignore` (unlikely — no such pattern in current `.gitignore`), or
- It was never `git add`ed when the components were committed.

Grep for a `lib/` pattern in `.gitignore` to rule out (a). If clean, cause is (b).

### Fix

1. Verify the current file contents are the standard shadcn `cn` helper (already confirmed above).
2. `git add frontend/src/lib/utils.ts`.
3. Commit with message: `fix(frontend): commit missing lib/utils.ts (cn helper) used by shadcn components`.

### Verification

```bash
# in a throwaway clone
git clone <repo> /tmp/fresh && cd /tmp/fresh/frontend
npm ci && npx tsc --noEmit    # should pass
npm run dev                   # should start without "Cannot find module '@/lib/utils'"
```

### Files touched
- `frontend/src/lib/utils.ts` (tracked for the first time)

---

## Issue 2 — MSW login handler URL mismatch

### Evidence

```
frontend/src/api/auth.ts:7
  apiClient.post<LoginResponse>('/api/v1/auth/login/json', credentials)

frontend/src/mocks/handlers/auth.ts:5
  http.post('*/api/v1/auth/login', async ({ request }) => { ... })
```

Client posts to `/api/v1/auth/login/json`. MSW handler matches `/api/v1/auth/login`. In MSW's matching, the handler path must match the full pathname — so login falls through to the real network (or 404s in dev).

### Root cause hypothesis

Backend has two login endpoints (form-encoded at `/login` and JSON at `/login/json` — the standard FastAPI OAuth2 pattern). The frontend was updated to use `/json` but the MSW handler wasn't. Confirm by checking `backend/app/api/v1/endpoints/auth.py`.

### Fix — decide which direction first

**Option A (recommended):** update the MSW handler to match the actual client call.

```ts
// frontend/src/mocks/handlers/auth.ts
http.post('*/api/v1/auth/login/json', async ({ request }) => { ... })
```

**Option B:** add *both* handlers so form-encoded and JSON login both work when MSW is on.

```ts
const loginHandler = async ({ request }) => { ... };
http.post('*/api/v1/auth/login', loginHandler),
http.post('*/api/v1/auth/login/json', loginHandler),
```

Recommend **B** — it mirrors the backend, zero-risk, and keeps the mock realistic if any code path still uses form-encoded login.

### Verification

1. `npm run dev` with MSW enabled.
2. Submit the login form with the mock credentials from `src/mocks/data/users.ts`.
3. Expect: `200`, token stored, redirect to `/`. No need to inject auth via localStorage.

### Files touched
- `frontend/src/mocks/handlers/auth.ts`

---

## Issue 3 — `tailwind.config.js` mixes CommonJS `require()` with ESM

### Evidence

```js
// frontend/tailwind.config.js
export default {                               // ESM
  ...
  plugins: [require("tailwindcss-animate")],   // CommonJS — line 73
};
```

```json
// frontend/package.json
"type": "module"
```

With `"type": "module"`, Node treats `.js` as ESM. `require` is not defined in ESM scope. Node 20 tolerates this for Tailwind's loader (which uses its own resolver). Node 22 is stricter and throws.

### Root cause hypothesis

The config was originally scaffolded as CommonJS (`module.exports = {...}`) and partially converted to ESM (`export default {...}`) without updating the plugin import.

### Fix — pick one

**Option A (recommended):** convert the plugin require to an ESM import.

```js
// frontend/tailwind.config.js
import animate from 'tailwindcss-animate';

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { /* unchanged */ },
  plugins: [animate],
};
```

**Option B:** rename to `tailwind.config.cjs` and revert the whole file to `module.exports = {...}`. Works but goes backward on module style.

**Option C:** set `"type": "commonjs"` in `package.json`. **Don't do this** — would cascade through Vite and the rest of the toolchain.

Go with **A**.

### Verification

```bash
cd frontend
nvm use 22                                    # or the pinned Node version
npm ci
npm run dev                                   # should start without ERR_REQUIRE_ESM
npm run build                                 # Tailwind should emit CSS normally; check `tailwindcss-animate` classes apply (e.g. accordion animations on Radix components)
```

### Files touched
- `frontend/tailwind.config.js`

### Follow-up — pin Node version

The root cause of this class of bug is that Node version isn't pinned. Add one of:

- `frontend/.nvmrc` containing `20` (or `22` if we fix Option A — then we can run on either).
- `engines.node` in `frontend/package.json`: `"node": ">=20.11.1"`.

Recommend both. Tiny change, removes a whole category of "works on my machine" issues.

### Files touched (follow-up)
- `frontend/.nvmrc` (new)
- `frontend/package.json` (add `engines` field)

---

## Execution order

1. **Issue 1 first** — without `utils.ts`, nothing compiles, so fixes 2 and 3 can't be verified.
2. **Issue 3 second** — unblocks Node 22 users (and keeps the fix clean before we touch more files).
3. **Issue 2 third** — verifies on a working build.
4. Pin Node version.
5. Commit each fix as its own commit so the changelog is legible.

## Out-of-scope observations (not blocking)

- The "Apps page shows error state due to MSW mismatch" note in the report is likely a second MSW handler gap, not the same issue. After Issue 2 is fixed, re-verify `/apps` — if it still errors, file a separate ticket; the handler for `/api/v1/apps` (or equivalent) may also be missing.
- Auth injection via localStorage (workaround Devin used) can be removed from verification steps once Issue 2 is fixed.

## Acceptance criteria for closing all three

- [ ] Fresh clone: `npm ci && npm run dev` starts on Node 20 **and** Node 22 with no errors.
- [ ] `npx tsc --noEmit` passes.
- [ ] Mock login form → dashboard flow works without touching localStorage.
- [ ] `git ls-files frontend/src/lib/utils.ts` returns the file path.
- [ ] `.nvmrc` or `engines.node` present.
