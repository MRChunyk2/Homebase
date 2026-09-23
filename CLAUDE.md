# Homebase — Advance Psychotherapy Practice

Internal staff app (roster, capacity, HR, payroll) for Advance Psychotherapy.
Live at https://advance-intranet.web.app · Firebase project: `advance-intranet`.

## Architecture

- **`public/index.html`** — the entire app: one self-contained HTML file (UI + logic).
  All edits to the app happen directly in this file.
- **`public/apply.html`** — public job-application form (no sign-in; writes to
  the `applications` collection).
- **`public/avail.html`** — public interview-availability picker (tokenized link).
- **`public/onboard.html`** — public new-hire onboarding portal (tokenized link;
  data in the `onboarding` collection, uploaded files in `onboardFiles`).
- **Data lives in Firestore, never in this repo.** The app boots behind Google
  sign-in (restricted to @advancepsychotherapy.org) and loads everything through
  the `window.storage` engine in the `<script type="module">` block at the bottom
  of index.html.
- **`firestore.rules`** — server-side access control (the real permissions;
  the in-app "Roles & Permissions" page is just the UI for it). Staff records are
  split across collections: `staff` (roster, all staff read), `staffPrivate`
  (address/DOB — self + admins), `staffCredentials` (CAQH/PECOS logins — admins
  only), plus `photos`, `userRoles`, `staffFiles`, `applications`,
  `availability`, `panelAvail`, `onboarding`, `onboardFiles`, `meetings`,
  `reviews`, `library`, and `kv/*` blobs (tiered by key).
- **`storage.rules`** — unused (Firebase Storage needs the paid Blaze plan,
  which is not enabled). Kept in the repo for a future upgrade. Onboarding
  uploads are stored in Firestore instead (`onboardFiles`, base64, one doc per
  file — images auto-compress; oversized files fall back to an "email HR"
  checkbox).
- **`build/`** — historical record of the June 2026 migration that split the data
  out of the original single-file app. The transform reads a source file that is
  not in this repo; do not re-run it. Reference only.

## Hard rules

1. **Never commit staff data.** No names-with-PII, addresses, DOBs, credentials,
   pay data, applicant records — in code, comments, tests, or fixtures. All data
   belongs in Firestore. The `seed/` directory is git-ignored on purpose; leave
   it that way.
2. **Always pull before making changes — a hard stop, not a suggestion.**
   Two people (Will, Michael) push to `main`, and edits often rewrite
   `public/index.html` wholesale, so building on a stale copy silently erases
   the other person's commits (this happened Aug 18 – Sep 23, 2026: four of
   Will's fixes were overwritten and had to be re-applied from git history).
   Every working session, in order:
   1. Pull in GitHub Desktop (or `git pull`) FIRST.
   2. Only then edit — and edit the freshly pulled copy, never one saved
      before the pull.
   3. Commit + push promptly once the change is verified. On Michael's side,
      pushing is not optional polish: it is the only road to the live site
      (see Publishing).
   Never restore an old git stash over current files, and never commit stray
   duplicates (`*-1.html`, `*-1.rules`, screenshot folders) — delete them.

## Publishing

Michael cannot deploy. The site goes live through this chain, and only this
chain:

1. **Michael**: edit (Cowork writes into this folder) → commit → **push**.
2. **Will**: pull → deploy from his machine:

```bash
firebase deploy --only hosting,firestore:rules --project advance-intranet
```

- There is no auto-deploy: pushing to GitHub does NOT publish by itself, and
  nothing on Michael's machine publishes. A change is live only after Will
  pulls and deploys it.
- When a change touches `firestore.rules` (new collection, permission change),
  say so in the commit message so Will knows the deploy must include
  `firestore:rules`, not hosting alone.
- Verify changes on the deployed site after Will's deploy (sign-in works on
  localhost too, serving `public/` locally).

Two collaborators (Will, Michael) push directly to `main`; no branch workflow.
