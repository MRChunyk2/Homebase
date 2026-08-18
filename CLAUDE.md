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
  data in the `onboarding` collection, file uploads in Firebase Storage under
  `onboarding/{token}/…`).
- **Data lives in Firestore, never in this repo.** The app boots behind Google
  sign-in (restricted to @advancepsychotherapy.org) and loads everything through
  the `window.storage` engine in the `<script type="module">` block at the bottom
  of index.html.
- **`firestore.rules`** — server-side access control (the real permissions;
  the in-app "Roles & Permissions" page is just the UI for it). Staff records are
  split across collections: `staff` (roster, all staff read), `staffPrivate`
  (address/DOB — self + admins), `staffCredentials` (CAQH/PECOS logins — admins
  only), plus `photos`, `userRoles`, `staffFiles`, `applications`,
  `availability`, `panelAvail`, `onboarding`, and `kv/*` blobs (tiered by key).
- **`storage.rules`** — Firebase Storage rules (onboarding portal uploads only:
  token-gated writes, @advancepsychotherapy.org reads).
- **`build/`** — historical record of the June 2026 migration that split the data
  out of the original single-file app. The transform reads a source file that is
  not in this repo; do not re-run it. Reference only.

## Hard rules

1. **Never commit staff data.** No names-with-PII, addresses, DOBs, credentials,
   pay data, applicant records — in code, comments, tests, or fixtures. All data
   belongs in Firestore. The `seed/` directory is git-ignored on purpose; leave
   it that way.
2. **Always `git pull` before making changes.**
3. After a verified change: offer to commit + push. Deploys are automatic.

## Publishing (auto-deploy)

Pushing to `main` deploys automatically via GitHub Actions
(`.github/workflows/deploy.yml`): hosting + Firestore rules + Storage rules.
Watch progress in the repo's Actions tab.

```bash
git pull                                   # before any edit
# …edit public/*.html or the rules files…
git add -A && git commit -m "…" && git push   # push = go live
```

One-time prerequisites (already done once set up):
- GitHub repo secret `FIREBASE_SERVICE_ACCOUNT` containing the Firebase
  service-account JSON (Firebase console → Project settings → Service
  accounts → Generate new private key).
- Firebase Storage enabled in the console (required by the onboarding portal
  and by `firebase deploy --only storage`).

Manual fallback (deploying from a laptop instead of CI):

```bash
firebase deploy --only hosting --account will@advancepsychotherapy.org
firebase deploy --only firestore:rules --account will@advancepsychotherapy.org
firebase deploy --only storage --account will@advancepsychotherapy.org
```

Verify changes by loading the deployed site (or serving `public/` locally —
sign-in works on localhost). Two collaborators (Will, Michael) push directly to
`main`; no branch workflow.
