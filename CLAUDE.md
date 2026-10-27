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
  data in the `onboarding` collection; uploaded files in Firebase Storage under
  `onboarding/{token}/…`, 10 MB each. Older uploads are base64 docs in `onboardFiles`).
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
  `reviews`, `library` (articles shown on Clinical Manual, Clinical
  How-Tos, and Employee Handbook — split by `cat`; the two manuals, `cmanual`
  and `manual`, are Super Admin–only and shown as a book with sign-offs),
  `libSignoffs` + `libSignatures` (manual sign-off rounds and signatures),
  `intakeProfiles` (Clinical Profile for Intake, one per clinician),
  `refLibrary` + `refLibraryFiles` (Learning & Reference and Paperwork &
  Templates items and their uploaded files), Payroll Review (Super Admin only:
  `payrollConfig`, `payrollPeriods`, `payrollImports` + `payrollRows` — the
  Valant export with patient names/notes stripped — and the create-only
  `payrollSnapshots` + `payrollPaid` for closed periods, plus `payStatements` —
  one read-only pay-period sheet per employee, readable by that employee: hours and
  FFS units only, no dollars, clients by code only), and `kv/*` blobs
  (tiered by key).
- **`storage.rules`** — Firebase Storage access control. The project has been on
  the Blaze plan since Sept 23, 2026; Storage is enabled (bucket
  `advance-intranet.firebasestorage.app`). **Uploaded file bytes go to Storage;
  their metadata (name, size, type, uploader, date, Storage path) stays in
  Firestore.** Paths: `refLibrary/{fileId}/{name}` (library files, 20 MB; admins
  write, all staff read), `staffFiles/{staffId}/{fileId}/{name}` (CEU certificates
  and Employee File documents, 20 MB; that person + admins), `onboarding/{token}/…`
  (new-hire portal, no sign-in, 10 MB). Rules read roles from Firestore
  `userRoles` via cross-service `firestore.get()`. Never base64 a file into a
  Firestore doc again — Firestore's 1 MB per-document limit is why the old cap
  was ~650 KB. Older base64 files (`b64` / `data` fields in `refLibraryFiles`,
  `staffFiles`, `onboardFiles`, staff `_files`) are still read by `fileOpen()`.
  Avatar `photos` stay in Firestore (160 px, small).
- **`build/`** — historical record of the June 2026 migration that split the data
  out of the original single-file app. The transform reads a source file that is
  not in this repo; do not re-run it. Reference only.

## Navigation (Oct 2026 reorg)

Five sidebar sections: My Homebase · Clinical Corner · HR Hub · Recruitment ·
Admin Logistics. Nav items carry `data-page`; `applyRoleVisibility()` hides
items via `canSeePage()` and hides any section left empty. Placeholder pages
("Coming soon") are listed in `PLACEHOLDERS`. New roles from the spreadsheet
(Prac Ops, Director, CTM/CPM) are NOT built yet — still therapist /
supervisor / admin / superadmin.

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
# when storage.rules changed:
firebase deploy --only hosting,firestore:rules,storage --project advance-intranet
```

- There is no auto-deploy: pushing to GitHub does NOT publish by itself, and
  nothing on Michael's machine publishes. A change is live only after Will
  pulls and deploys it.
- When a change touches `firestore.rules` (new collection, permission change),
  say so in the commit message so Will knows the deploy must include
  `firestore:rules`, not hosting alone. Same for `storage.rules` → `storage`.
- index.html is one huge file with two script blocks and sign-in wired at the
  very end: an uncaught top-level error stops everything after it (this once
  took the site down). New code goes in functions with try/catch — no top-level
  work.
- Verify changes on the deployed site after Will's deploy (sign-in works on
  localhost too, serving `public/` locally).

Two collaborators (Will, Michael) push directly to `main`; no branch workflow.
