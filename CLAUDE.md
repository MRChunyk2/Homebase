# Homebase — Advance Psychotherapy Practice

Internal staff app (roster, capacity, HR, payroll) for Advance Psychotherapy.
Live at https://advance-intranet.web.app · Firebase project: `advance-intranet`.

## Architecture

- **`public/index.html`** — the entire app: one self-contained HTML file (UI + logic).
  All edits to the app happen directly in this file.
- **Data lives in Firestore, never in this repo.** The app boots behind Google
  sign-in (restricted to @advancepsychotherapy.org) and loads everything through
  the `window.storage` engine in the `<script type="module">` block at the bottom
  of index.html.
- **`firestore.rules`** — server-side access control (the real permissions;
  the in-app "Roles & Permissions" page is just the UI for it). Staff records are
  split across collections: `staff` (roster, all staff read), `staffPrivate`
  (address/DOB — self + admins), `staffCredentials` (CAQH/PECOS logins — admins
  only), plus `photos`, `userRoles`, and `kv/*` blobs (tiered by key).
- **`build/`** — historical record of the June 2026 migration that split the data
  out of the original single-file app. The transform reads a source file that is
  not in this repo; do not re-run it. Reference only.

## Hard rules

1. **Never commit staff data.** No names-with-PII, addresses, DOBs, credentials,
   pay data, applicant records — in code, comments, tests, or fixtures. All data
   belongs in Firestore. The `seed/` directory is git-ignored on purpose; leave
   it that way.
2. **Always `git pull` before making changes.**
3. After a verified change: offer to commit + push, then deploy.

## Workflow

```bash
git pull                                   # before any edit
# …edit public/index.html or firestore.rules…
git add -A && git commit -m "…" && git push
firebase deploy --only hosting --account will@advancepsychotherapy.org          # app changes
firebase deploy --only firestore:rules --account will@advancepsychotherapy.org  # rules changes
```

Verify changes by loading the deployed site (or serving `public/` locally —
sign-in works on localhost). Two collaborators (Will, Michael) push directly to
`main`; no branch workflow.
