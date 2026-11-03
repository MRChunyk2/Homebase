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
  `payrollSnapshots` + `payrollPaid` for closed periods (now written by Pay Period Upload, see
  below), plus `payStatements` —
  one read-only pay-period sheet per employee, readable by that employee: hours and
  FFS units only, no FFS dollars, clients by code only; shown on HR Hub → Pay Period
  Snapshot, where only $25/hr meeting time shows dollars), and `kv/*` blobs
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

## Capacity math (Capacity Dashboard)

Goals are built day by day from the capacity year start (`capGoalTo`): 1140 × (Weekly
Capacity ÷ 25) ÷ 364 per day × new-hire ramp (25/50/75/100% in 15-day steps), and 0 on leave
days, before hire, and after the term date. Timeline data lives on the `staff` record (dates
only, no reasons): `_capHist` [{from, weekly}] (Weekly Capacity changes — earlier days keep
the old pace), `_leaves` [{start, end}], `Notice Date`, `Term Date`. They're entered from the
profile edit form when Status / Weekly Capacity changes, or fixed in the admin
"Capacity adjustments" card on a clinician's dashboard. Unadjusted staff keep the even
quarter checkpoints (¼, ½, ¾, full). Capacity-tier review warning: catch-up > 12 extra
hrs/week over the next 90 days (full-time → step down a tier; part-time → seek supervision).

## Pay periods

The official 2026–2028 pay-period calendar is hard-coded in `APP_PAY_PERIODS` (verified by
HR; never changes) and drives `ALL_PPS` (index 0–25 = 2026 = the capacity year's data index).
Every pay-period menu shows past periods and at most 3 months ahead (`APP_PP_AHEAD_MONTHS`,
`appPPInMenu`). Payroll Review periods are created by picking from this calendar.

Capacity years reset on PP YYYY-01 (`CAP_YEAR`, `CAP_YEAR_START`, `CAP_PP_OFFSET`): the year is
the one today's pay period belongs to; admins can open an earlier year from the year picker
(Capacity Dashboard / Payroll Processing — per browser tab via sessionStorage, reloads the
page). Each year has its own stores: 2026 = kv/app_clinical_hours, app_group_hours,
app_payroll_detail; later years append `_YYYY` (`capStoreKey`). firestore.rules gives
`app_payroll_detail_YYYY` the same Super Admin–only tier as `app_payroll_detail`.

## Pay Period Upload + Service Code Rules (Nov 2026)

Replaces Payroll Review and Payroll Processing (their nav items are gone; old code still in
the file, unused). Admin Logistics → **Pay Period Upload** (`renderPPU`, Super Admin): pick an
official pay period, upload that period's Valant appointment export (rows outside the period
are ignored; patient NAMES are never stored — only the client code in parentheses), review
every employee, correct rows (exclude / change code / not a duplicate — reason required),
link Valant ProviderIDs to staff, then close. All math comes from **Service Code Rules**
(`renderCodeRules`) — the "Cap Hours Formula for Homebase" sheet, editable and versioned in
`payrollConfig/codeRules` (seeded from the sheet with 11111 = paid no show: 1 FFS hr, 0
clinical; 11112 = unpaid no show: 0/0; SUP PAID = "Paid Supervision": 1 FFS hr, 0 clinical;
SUP UNPAID = "Unpaid Supervision": tracked count only). Per appointment: category hours = % of FFS; clinical
credit = Clinical Hours Count for Cap (no-shows always 0); differential = 1 per appointment
when the rule allows it AND it starts ≥ 5 PM Mon–Fri or any time Sat/Sun (add-ons never add
one); additional comp from the sheet ($ per unit); bonus = clinical hrs over 50 × $20 (pay
settings on the rules page). No FFS rates anywhere: FFS is reported as hours ("Total FFS hours
for Paychex" = categories + paid no shows + paid supervision + FFS-rate meeting time). Meeting and Admin Time is
included and marked PAID on close. Closing writes an immutable snapshot
(`payrollSnapshots/ppu_<PP>_v<n>`: rules version, links, corrections, results), publishes
`payStatements` (kind 'ppu', shown on Pay Period Snapshot — hours only, $ only for $25/hr
meetings), and writes each employee's clinical hours into the Capacity Dashboard for that
period (group factor no longer applied — the sheet sets each code's credit). Reopen = new
version. Storage reuses the existing Super Admin–only payroll collections (no rules change).

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
- Unsaved-changes guard (`hbConfirmLeave`, site-wide): typing in an edit form marks
  it unsaved and navigation/closing a record/closing the tab asks first. New edit
  forms must be covered by `HB_EDIT_MATCH` (ids/containers) or they won't be guarded.
- Theme follows the Advance Psychotherapy brand kit: Deep Navy #122B67 (sidebar,
  headers, primary buttons) + Teal #18A9B6 (active/highlight) + white; Coral
  #E46756 / Orange #F2A54B / Aqua #5EBAC8 only as small accents; Montserrat for
  headings, Open Sans for body. No off-brand colors. Exception — the SIDEBAR is
  "dusty navy" (#3a4a6b, light text, emoji icons, no accent colors; only the
  section headers are emphasized), by Michael's request.
- index.html is one huge file with two script blocks and sign-in wired at the
  very end: an uncaught top-level error stops everything after it (this once
  took the site down). New code goes in functions with try/catch — no top-level
  work.
- Verify changes on the deployed site after Will's deploy (sign-in works on
  localhost too, serving `public/` locally).

Two collaborators (Will, Michael) push directly to `main`; no branch workflow.
