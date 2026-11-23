# Homebase — Advance Psychotherapy Practice

Internal staff app (roster, capacity, HR, payroll) for Advance Psychotherapy.
Live at https://advance-intranet.web.app · Firebase project: `advance-intranet`.

## Current state (Nov 10, 2026) — read this first
_Where this section and older notes below disagree, this section wins. The dated sections further down are the change log._

**Menu (left nav, role-gated by `canSeePage` + Roles & permissions)**
- **My Homebase:** My Homebase (widgets: Site & emergency, Needs your attention ticker, Your capacity, Clinical Profile for Intake, My office, Meeting & admin time, Practice calendar, Latest news, Suggestion box) · My Team (Supervisor+) · Clinical Profile for Intake · Office Bookings (hidden for Format = "Virtual Only").
- **Clinical Corner:** Capacity Dashboard · Discharge & Transfer (coming soon) · Clinical Policies & How-To Manuals · Paperwork & Templates · eCANS (coming soon) · Therapy Thrive (coming soon) · Learning & Reference.
- **HR Hub:** Roster (Supervisor+, scoped) · My Employee File · HR Dashboard (Supervisor+) · Onboarding (admins) · Meeting and Admin Time · Pay Period Snapshot · Employee Handbook.
- **Recruitment** (admins): Recruitment Dashboard · Candidate Management.
- **Admin Logistics:** Homebase Settings (Practice alerts · News & announcements · Events calendar · Office settings · Roles & permissions · Bulk record upload · Payroll Settings [Super Admin]) · Supply Ordering (admins) · Leadership Dashboard · Payroll Processing (Super Admin) · Intake Finder · Report Center (coming soon).
- Old addresses redirect: `#meetings-hr` → Payroll Processing › Meeting & Admin Time; `#coderules` → Homebase Settings › Payroll Settings; `#ceu-upload` → Homebase Settings › Bulk record upload; `#clin-howtos` → Clinical Policies (How-To tab).

**Main modules in `public/index.html` (function prefixes)**
- `ppu*` Payroll Processing (5 steps: upload Valant CSV → verify staff links → approve meetings/groups/reimbursements → close → Paychex CSV); `PR.*` shared payroll engine; `cr*` Payroll Settings; `ps*` Pay Period Snapshot. Payroll Review page is gone but its `pr*` code stays — `prOpenSheetForPP` (Capacity Dashboard pay-sheet link) still uses it.
- `mtg*` Meeting and Admin Time (staff) — every staff entry needs payroll approval; group sessions (`isGroup` type) live in the same `meetings` collection.
- `ob*` Office Bookings, `obs*` Office settings · `ip*` Clinical Profile for Intake · `if*` Intake Finder · `cap*` Capacity Dashboard · `cl*` My Team · `home*`/`hcal*` My Homebase · `hbm*` Homebase Settings · `sa*` staff alerts (realms, billing client codes, hard stop) · `ceuUp*`/`bulk*`/`docsListHtml` Bulk record upload + Employee File documents · `lib*` manuals · `perm*`/`hbCan` roles & permissions.
- Startup helpers `seedSuperAdmins` / `promoteOnboardingToActive` are self-running (IIFEs) — not dead code; don't remove.
- Styles: one site-wide tab style (`.hb-tabs` / `.hb-subtabs`, option D); several modules inject their own CSS (`ppuCss`, `ipCss`, `mtgCss`, `obCss`, …).

**Data**
- Firestore collections in use: staff, staffPrivate, staffCredentials, photos, userRoles, applications, availability, onboarding, onboardFiles, staffFiles, staffAlerts, meetings, officeBookings, intakeProfiles, panelAvail, reviews, library, libSignoffs, libSignatures, refLibrary, refLibraryFiles, payrollConfig, payrollPeriods, payrollImports, payrollRows, payrollSnapshots, payrollPaid, payStatements, kv.
- Main kv keys: app_staff, app_config, app_roles, app_perm_roles, app_photos, app_recruit, app_comp_checklist, app_comp_data, app_payroll_detail(_YYYY), app_clinical_hours, app_practice_stats, app_team_stats, app_code_guide, app_events, app_news, app_practice_alerts, app_office_rooms, app_office_cfg.
- `suggestions` collection: Suggestion box entries {text, cat, anon, name, sid, at, status new/read/done, note}; anyone creates, only Super Admins read (Homebase Settings → 📬 Suggestions; new ones show in their Needs your attention).

**Testing / safety net** — `Claude outputs/cleanup/`: `sweep.js` (every page × 5 role views: JS errors, blank pages, odd text) and `flows.js` (13 key flows) run against the preview build; `compare.py` diffs two sweep results; baseline + per-batch results are saved there. Restore point before the cleanup: git tag `pre-cleanup-2026-11`.

**Known gaps (not bugs introduced by the cleanup)**
- Office Bookings approvals rely on CTMs having the **Supervisor** access level (rules allow Supervisor+ to approve); a CTM left at Therapist level can see but not approve.
- Homebase Settings sections are writable only by Admins at the database level, even if a custom role is given "Manage Homebase content".

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

Nov 2026 changes: **Leadership Dashboard** moved to Admin Logistics (admin only). New
My Homebase page **My Team** (page id `clin-leadership`, `renderClinLeadership`, `clScope`): Admins / Super
Admins / Senior Leadership see every team (team picker); CTMs and Program Managers see their
whole team plus their supervisees broken out (flagged "other site"); Clinical Supervisors /
Supervisors see their supervisees (Supervisor field, overrides, and Reports To). Tiles, alerts
(tier review, behind, licenses ≤60 days, leave/offboarding/ramping) and insights.
Alerts are grouped **by person** in three bands (Needs action / Keep an eye on / FYI), each
person's alerts as chips. Note status YTD per person (signed ≤3 days %, avg days to sign,
unsigned at close, no-show %) comes from `kv/app_team_stats` = {ppId:{staffId:counts}} written
by `ppuSaveTeamStats` when a pay period closes (counts only — no clients, dates or pay; rules:
Supervisor permission level and up). Note alerts: unsigned ≥1 (FYI) / ≥5 (watch); <80% on
time (watch) / <60% (action); no-show ≥10 pts above practice (FYI). "Your team vs the
practice" card compares attainment, on-pace %, clinical hrs per clinician per pay period and
the note/no-show measures (`clYtd`, `clRates`, `clLoadStats`; cache `CL.stats`, reset on page open).
**My Homebase is personal at every permission level** (no practice-wide alerts): Needs your
attention, Your capacity, Meeting & admin time (`homeMeetingsHtml`), Your Team Site, Emergency
quick reference by site (`homeEmergencyHtml`, site picker), quick links, announcements, and
a collapsed suggestion box. **Performance Reviews are hidden** (`HB_REVIEWS_HIDDEN`). Manuals:
"Clinical Policies Manual" + "Clinical How-To Manual" (eCANS bookmarked under How-To, removed
from nav). License alerts read the profile's `Lic Exp Date` first. Differential/bonus
eligibility: profile field `Diff Bonus Eligible` (Yes/No/blank = default: not eligible for
supervisor/CTM/PM/Senior Leadership roles and salaried staff — `payEligible`); ineligible staff
are tracked but paid $0 on Pay Period Upload and their snapshot doesn't mention it.

**Custom roles** (Roles & Permissions → Custom roles, `renderPermBuilder`, kv/app_perm_roles):
a role = an access level (therapist/supervisor/admin/superadmin — still what the server allows,
synced to userRoles via ROLE_MAP when a Super Admin assigns people) + the pages it shows + its
abilities (`hbCan`: edit-profiles, see-files, see-comp, edit-library, manage-permissions).
`canSeePage` checks the viewer's custom role first, else `canSeePageBase` (the built-in rules).
Visibility only — firestore.rules are unchanged; the builder flags pages/abilities the chosen
access level can't load. Super Admins always keep the full view; only a Super Admin can create
or assign a Super Admin–level role; "Manage roles & permissions" can be delegated.

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

## Pay Period Upload + Payroll Settings (Service Code Workbook) (Nov 2026)

Replaces Payroll Review and Payroll Processing (their nav items are gone; old code still in
the file, unused). Admin Logistics → **Payroll Processing** (was Pay Period Upload) (`renderPPU`, Super Admin): pick an
official pay period, upload that period's Valant appointment export (rows outside the period
are ignored; patient NAMES are never stored — only the client code in parentheses), review
every employee, correct rows (exclude / change code / not a duplicate — reason required),
link Valant ProviderIDs to staff, then close. All math comes from **Payroll Settings (Service Code Workbook)**
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
Closing also saves a no-names practice aggregate per pay period to `kv/app_practice_stats`
(all staff read). The Capacity Dashboard's **Progress this year** card (`capProgressFill`,
replaced the "Sessions by Type" placeholder) shows notes signed, signed within 3 days, avg
days to sign, no-show rate, evening/weekend share, clinical hrs per pay period and sessions
by type — the clinician's own numbers from their payStatements (self + Super Admin), each
compared with the practice average.

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

**Clinical Profile for Intake — Diagnostic Realms & Exclusions (Nov 2026):** scale is
Experience / confidence level Low · Moderate (default, unmarked) · High, plus Prefer not to
treat (stored "low" | "" | "exp" | "no"; old "cert"/"spec" read as High — certifications live
on the Modalities step). Identity-based items (`IP_NO_DECLINE`: LGBTQ+, Transgender /
Nonbinary, BIPOC, Religious / Spiritual, Neurodivergent Adults, Gender Identity Exploration)
can't be declined; old "no" marks on them are cleared on read and ignored by the finder.
Low = −1.5 score + a warning in the finder (not an exclusion). Renames via `IP_RENAMED`
(Religious / Spiritual incl. spiritual abuse; Eating Disorders; ARFID spelled out); "Recent
Violence" split into victim / perpetrator via `IP_SPLIT` (old mark copies to both).

**HR Dashboard** is hidden from the Therapist level (`canSeePageBase`). **Built-in levels are
editable** (Roles & Permissions → Roles & page access): a Super Admin can change the pages and
abilities of Therapist / Clinical Supervisor / Admin; stored as `base` in `kv/app_perm_roles`
and applied through `permViewerRole()` (custom role first, then the edited level, else the code
defaults in `canSeePageBase`/`hbCan`). "Reset to default" deletes the override. Super Admin is
never editable. Visibility only — server rules still follow the access level.

**My Team view switch (all-teams level):** View = My supervisees (default when you have any) ·
All teams · a team (`CL.team` '__mine' | '__all' | team code; `clSetTeam`, remembered in
localStorage `hb_myteam_view`). Alerts, tiles, comparison card and tables follow the view.

**Nov 2026 — Payroll Processing / Pay Period Snapshot layout:** "Pay Period Upload" page renamed
**Payroll Processing** (page id still `ppu`); its period menu is grouped by year (the practice YTD graphs were removed at Michael's request; `ppuFillYtd` is unused). Pay Period Snapshot: navigator (‹ Newer / menu grouped by year /
Older › / Find by date — `paySnapStep`, `paySnapFindDate`) replaces the chip wall; statement
(`ppuStatementHtml`, styles `psCss`) = three colored bands: **Compensation for Clinical Hours and
Credits towards Capacity** (navy: Clinical Hours Credited, FFS Hours Paid = sessions + paid
no-shows, paid/unpaid no-shows, FFS hours paid by service type) → **Differentials and Bonuses**
(orange #F2A54B: Evening/Weekend One-Hour Sessions, Over 50 Clinical Hours in a PP, CANS &
Additional Clinical Comp units, Anniversary Bonus placeholder — "Coming soon") → **Paid Time,
Supervision and Meetings** (teal: supervision paid/unpaid, meetings & admin at $25/hr and at FFS,
meeting list, all-FFS total line). The Appointments list (collapsed, `.ps-appt`) sits inside the navy clinical band. Units: hours always "0.00 hrs",
counts "n session(s)"/"n unit(s)" → Appointments (collapsed). The two
sections are distinct colored bands (`.ps-band.clin` navy, `.ps-band.paid` teal). No charts on the
snapshot (removed at Michael's request); `psBarChart` is used only by Payroll Processing's YTD.
Snapshot ↔ Capacity Dashboard: prominent buttons both ways (`paySnapToCapacity`, `paySnapGo(sid)`).

**Payroll Settings** (was Service Code Rules; page id still `coderules`): tabs **Differentials &
Bonuses** (`crSettingsHtml`: differential $/session, weekday evening start, weekends toggle
`settings.weekends`, per-code "When it earns the differential" = Evenings & weekends | Any time
→ row field `diffAny`, one-click "60-min private-pay codes (incl. EMDR) → Any time" via
`crIsPP60`/`crMarkPP60`; over-threshold bonus threshold & $/hr; CANS & additional comp $/unit per
code; Anniversary Bonus placeholder) · **Service Code Workbook** (the editable sheet) · **Version
history**. All of it saves as one versioned `payrollConfig/codeRules` doc. Engine: a line earns the
differential when its code has `diff` and (`diffAny` OR weekend (if `weekends`) OR start ≥ eveStart).
CSV export adds a "Differential Any Time" column; import keeps existing `diffAny` if the column is absent.

**Anniversary bonus:** $`annivRate` (default 100) × years at APP, paid in the first pay period that
starts after the hire-date anniversary (`ppuAnnivFor`; hire date = profile 'Date of Hire'; Feb 29 →
Feb 28; not paid if Term Date is before the pay period). Everyone gets it — not tied to the
differential/bonus eligibility flag. Settings: `settings.anniv` on/off + `annivRate` (Payroll
Settings → Differentials & Bonuses, with a "Coming up" list). Engine sets `E.anniv` {years,c,date,hire};
`R.annivs` lists everyone due that period (card on Payroll Processing flags people not in the
Valant upload so Payroll adds them in Paychex by hand); CSV has Anniversary Bonus years/$; the
snapshot's Differentials and Bonuses band shows it.

**Snapshot $ for differentials & bonuses:** statements now carry diffC / bonusC / addC (cents) and
diffRate / bonusRate. `psMoney(S)` reads them (older statements fall back to hours × rate; CANS $
unknown → "—"). Differentials and Bonuses band shows $ per tile; "This pay period" and "Year to date" totals sit
in the orange header (`.ps-bht`; opt.ytd = that year's statements through the selected one). `ppuUsd` now
formats with thousands separators.

**My Homebase is all widgets (Nov 2026):** Quick Access removed. Rows: (1) **Your Site & Emergency**
(left: site, weather, team leads, emergency numbers with a site picker — `homeEmergencyInner`) +
right column = **Needs your attention** ticker (critical items pinned; the rest show 3 at a time and
rotate every 7s, pause on hover, Next / Show all — `homeAlertsClamp`/`homeAlertsStep`) with Your
capacity · Meeting & admin time under it; (2) **Practice calendar**; (3) **Latest Practice News and
Updates** + Suggestion box. Sleek pass: flat cards (8px radius, 1px border, 3px brand-color top line
via --acc), one neutral header band, no emoji chips (`.hs-ic` hidden), small radii everywhere.
**Staff alerts:** Employee File → "🔔 Issue alert" (`saOpen`; capability `issue-alerts`, Super Admin
by default, grantable in custom roles/levels). Firestore `staffAlerts` {sid,title,msg,level
critical|important|info,due,issuedBy,issuedAt,status open|done,ackAt,ackBy} — RULES: admins
read/write; the employee reads own and may only set status 'done'. Shown first in Needs your
attention (`#home-adminalerts`, `homeLoadStaffAlerts`); critical = red + pinned + card top line
turns red; employee clicks "Mark done". **Practice calendar**
(`homeCalendarHtml`/`hcalPaint`/`hcalLoad`). Events in `kv/app_events` = {events:[{id,title,
date,end (multi-day),allDay,start,endTime,location,desc,scope:'all'|teamCode,…}]} — everyone
reads, Admins/Super Admins add/edit/delete (kv default tier; no rules change). Practice-wide events
show to all; team events to that team; Admins see all with a team filter. Month grid (dots: teal =
practice-wide, orange = team) + "Coming up" (45 days) or the picked day. A Google Calendar feed
can merge into HCAL.events later (same shape).

**Employee File layout (admins only):** a row under the header (`profileAdminBarHtml`, `#m-adminbar`,
PF_MODE 'menu') with **Alerts & flags** on the left (`pfLoadFlags`: open staff alerts — click to manage —
plus automatic flags: license lapsed/expiring ≤60 days, on leave / offboarding / onboarding, missing
items, capacity tier review / behind) and one **⚙ Admin actions ▾** menu on the right holding everything:
Record (Edit record, Change photo, Delete record…), Alerts (Issue / Manage), Employment & capacity
(capacity change, leave dates, offboarding dates), Files & records (Training & CEU, Non-Private Docs,
Comp & Benes tabs), Go to (Capacity Dashboard, Clinical Profile for Intake, Pay Period Snapshot), Access
(level, "Change access level…", See Homebase as this person, All roles & permissions). Items show only
when the viewer has that ability. Therapists/supervisors see no row. Tabs unchanged.

**Homebase Settings (Admin Logistics; page id still `admin`, nav "🛠️ Homebase Settings"):** where
admins update what employees see. Tabs (`HBM.sec`, `hbmShell`, `hbmGo(sec)`): **Practice alerts**
(kv `app_practice_alerts` {items:[{id,title,msg,level critical|important|info,link,start,end,
aud:{type all|teams|groups,teams,groups}}]} — shown in Needs your attention (`#home-practicealerts`,
`homeLoadPracticeAlerts`) while start ≤ today ≤ end, no acknowledgment; groups = clin / sup /
nonclin / admin via `hbmGroupsOf`; also lists open individual staffAlerts via `alertStore.all`),
**News & announcements** (kv `app_news` {items:[{id,title,body,link,linkLabel,date,until,ticker,pinned,by}]}
— newest 4 in Latest Practice News (`#home-news`, `homeLoadNews`), all on the Announcements page
(`renderAnnouncements`), ticker:true items scroll in the top ticker; falls back to CONFIG.announcements /
tickerItems until the first post), **Events calendar** (same kv `app_events` as the homepage calendar),
**Roles & permissions** (the old page, `renderAdminRoles`; Super Admins or manage-permissions). Access:
capability `manage-homebase` (Admins + Super Admins by default, grantable to custom roles). kv default
tier (all staff read, admins write) — no rules change.

**Paychex entry report** (Payroll Processing → "📄 Paychex entry report", open or closed period; `ppuPaychexReport`,
`ppuPaychexRows`, CSV `ppuPaychexCsv`, print): one row per employee — FFS hours (sessions + paid no-shows +
meetings at FFS), Bonus $ (differential + over-threshold + CANS/additional + anniversary; hover for the
breakdown; anniversary-only rows for people not in the upload), Admin ($25/hr meeting hours and $), Paid
supervision hours; totals row. **Service code guide** on the Pay Period Snapshot ("📋 How each service
counts", `psGuideOpen`): plain table per Display Heading — capacity credit, % of FFS paid, extras — from
kv `app_code_guide` (no rates; published by `ppuPublishGuide` when Payroll Settings are saved or loaded with
a newer version).

**Manual group sessions** (Payroll Processing → "👪 Group sessions" tab; the three tabs Employees / Meeting &
Admin Time / Group sessions are now large highlighted buttons, `ppuTabsHtml`): group sessions aren't on the
Valant export, so payroll adds them per pay period — clinician, date (inside the period), start time, a
group service code from the workbook (G 90853 first), # clients, notes. Stored on the period doc as
`manualGroups` [{id,sid,date,start,code,clients,notes,by,at}] (audited); `ppuCompute(..., pp, groups)` scores
each like a Valant row (clinical credit, FFS %, differential timing) as a line with `manual:true` (counts as
signed for note stats). Entries can be added before the Valant upload; closed periods are read-only.

**Meeting & admin time — payroll entry + staff self-entry date gate:** `MTG_SELF_OPENS='2026-11-23'`
(`mtgSelfOpen()`, local midnight). Before then the staff Meeting and Admin Time page shows "Opens Monday,
November 23 — payroll is entering it for you" instead of the form (`mtgSubmit` is blocked too). Payroll
Processing → Meeting & Admin Time tab has an "Add meeting & admin time" form (`ppuMtgFormHtml`, `ppuMtgAdd`):
employee, type (CONFIG.meetingTypes → rate), date in the period, start/end, notes — saved to the same
`meetings` store with enteredBy:'payroll' (shown as "Payroll", removable); staff entries show as "Staff"
and prepopulate the tab from 11/23. Payroll Processing now computes the period whenever there's anything
for it (Valant rows, manual groups, or meeting time), so these tabs work before the Valant upload.

### Paychex columns, meeting categories, auto anniversary (Nov 2026)
- **Meeting & Admin Time types** (CONFIG_DEFAULTS.meetingTypes, set in code): `ffs-mtg` Meeting paid at FFS (approval: staff entries pending until payroll Approves; payroll entries auto-approved), `interim` Interim Supervision Hours provided (only for profile role *Interim Hourly Supervisor*; rate 'interim'), `consult` Consultation Group / Team Meetings ($25), `group-admin` Group Admin Time ($25, optional group name; no cap). Interim supervision is paid at 1.25× the person's FFS rate (hours only in Homebase).
- Each type has `aliases` so the old Google Form labels map on CSV import (`mtgTypeOf` falls back to alias match): Clinical Team Meetings / Program-Specific / Approved Admin Time for Special Project → consult; Group Preparation Time → group-admin; Administrative Meeting (FFS) → ffs-mtg; Temporary Supervision Provided → interim; "Other" → no category (warning until a rate is set). Import preview shows the mapping per label.
- **Paychex entry report** (`ppuPaychexRows`): FFS = session hours excluding group codes; Bonus $ = differentials + over-threshold + anniversary; Admin = $25/hr meeting hours + meetings at FFS (hours) + CANS/additional comp ($); group codes = `ppuIsGroupCode` (code starts "G "/"GV " or heading contains "group"), tracked as E.grpFfs; Groups = all group headings incl. manual groups; Paid No Shows; Paid supervision = SUP PAID + interim hours; Professional / Expense Reimbursement = placeholder columns (not tracked yet). CSV carries the breakdown columns.
- **Anniversary bonus**: `annivStart` setting (default 2027-01-01) — only pay periods starting on/after it pay automatically. On close, `ppuAnnivAlerts` writes a 🎉 staffAlert (kind 'anniv', ppId, level info) per person, deduped per pay period.
- Snapshot shows an "Interim Supervision Provided" tile when there are interim hours.
- CANS/additional comp is admin pay: snapshot shows it under Paid Time and Meetings and it is no longer in the bonus total.

### Meeting & Admin Time rebuild + HR page retired (Nov 2026)
- **Employee page** (`renderMeetings`, `.me-*` CSS in `mtgCss`): hero with this-period/YTD stats; 3-step form (type cards filtered by role with `desc` from meetingTypes → date + start/end or length chips → notes); "Submit & add another"; My time list for current/previous period with Edit (re-add then delete old — staff can't update per rules) and Delete for their own unpaid entries; earlier periods summary; Training reimbursement "coming soon" bookmark card. Open now — `MTG_SELF_OPENS` is empty (set a date to lock entry until then).
- **Meeting and Admin Time (HR) page retired**: nav hidden; `showPage('meetings-hr')` redirects to Payroll Processing → Meeting & Admin Time. Old functions left in place but unused.
- **Payroll Processing → Meeting & Admin Time**: CSV upload (`ppuMtgImport*`) like the Valant upload — only rows dated in the selected pay period import; others counted by period; duplicates (sid+date+start+type) skipped; names matched via `capImpMatch`; PAID rows get `paidPeriod`; per-label mapping preview. Payroll can Edit (`ppuMtgEdit`, mtgStore.update) or Remove any entry while the period is open.
- **Training Reimbursement tab** (`ppuReimbHtml/Add/Del`): period doc `.reimb=[{id,sid,date,desc,amountC,notes,by,at}]` → Paychex report "Professional Reimbursement" column (`ppuReimbBySid`).
- More aliases: 'ffs rate'/'at ffs' → ffs-mtg; 'admin rate' → consult.
- Entry form v2: step 1 is a one-column list using meetingTypes `short`/`icon`/`ex`/`order` (friendly names; the official `label` is what's saved); step 2 = Day (Today/Yesterday chips + date), Started (15-min select 7 AM–9 PM), How long (15m–3h chips + Other… up to 8h). End time is computed (`mtgDurPreview` → hidden #mtg-end).

### Group sessions logged by clinicians + Payroll Settings moved (Nov 2026)
- New meeting type `group-session` (`isGroup`, label 'Group session (not in Valant)', approval). Staff form shows group name, service code (group codes from published `app_code_guide`, fallback list) and headcount. Record adds `code`, `headcount` (and omits payDate/payMethod to stay under the 20-field rules limit).
- `ppuCompute`: group records are pulled out of the meetings loop (`grpRecs`). Pending (approved===false) → warning only. Codes in Payroll Settings `groupHeadCodes` (default G 90853, GV 90853, G PP 60, GV PP 60) pay `headcount × groupRate` ($17) → `E.grpHeadC/grpHeadN`, capacity credit from the workbook, no FFS hours. Other group codes run through `addRule` (workbook FFS + capacity). No differential on logged groups. Close marks `E.grpItems` PAID.
- Payroll Processing → Group sessions tab now lists these records (Approve / Edit / Remove, payroll can add). Old period-doc `manualGroups` still count and show as "older entry".
- Paychex Groups column = FFS group hours · per-participant $. Snapshot shows Group Sessions + Group Pay tiles.
- **Payroll Settings** is now a section of Homebase Settings (super admins): `hbmSections` 'payset' renders `renderCodeRules` into `#coderules-body` inside the section. The nav item is hidden and `showPage('coderules')` redirects there. New "Group Sessions" card (groupRate, groupHeadCodes).

### Nav + My Homebase widget (Nov 2026)
- Clinical Profile for Intake moved from Clinical Corner to the My Homebase nav section (same page id `intake-profile`).
- My Homebase widget `homeIpWidgetHtml` / `homeLoadIpWidget` (clinicians only, sits in `.hm-pair` with capacity + meetings): intake status pill, freshness vs IP_STALE_DAYS, open hours (virtual/in person), ages · modalities count, high-experience specialties, Update request / ✓ Still accurate buttons.
- Group entry rules: headcount = clients **marked as attending** (no no-shows / absent members); groups are always **1 hour** (staff form fixes length at 60 min; payroll form has no end time). Step 3 for groups asks "Anything payroll should know about this group?"; notes show on the payroll Group sessions list.
- Payroll Processing → Group sessions: logged entries listed first with "✓ Approve all"; hand entry is behind "+ Add a group by hand"; a hint links to later pay periods that also have logged groups. Pending groups produce one combined "For review" line.

### Tabs — one style site-wide (Nov 2026, option D)
- Global CSS block at the end of the main `<style>`: **level 1** `.hb-tabs > .hb-tab(.on)` (light navy strip, bold 14.5px labels, 4px orange bar under active) and **level 2** `.hb-subtabs > .hb-subtab(.on)` (plain row, teal underline). Counts use `.hb-n`.
- Older classes are mapped onto these with `!important` (pages inject their own CSS at render): L1 = .hbm-tabs/.hbm-tab, .tab-bar/.tab-btn(-active) (Employee File, roster popup, Candidate Management), .ppu-bigtabs/.ppu-bigtab (Payroll Processing views — subtitle hidden), .ip-tabs, .pr-tabs; L2 = .ppu-tabs/.ppu-tab (Payroll Settings, drill-down), .me-tabs, .offer-tabs/.offer-tab.active.
- Converted inline tab sets: Roles & permissions sub-tabs (`adminTabsHtml`), Treatment Profile tabs (`mkTab`), library category tabs (Clinical Policies / How-To, books). New tab sets should use `.hb-tabs`/`.hb-subtabs` directly.

### Payroll Processing layout (Nov 2026)
- Top bar (`.ppu-bar`): pay period select + status chip, Paychex entry report / Download CSV, Payroll Settings link.
- Open periods show a numbered checklist (`ppuStepsHtml`): ① Upload Valant export ② Link providers (unmatched listed inline; View all) ③ Review & approve (group sessions / FFS meetings awaiting approval with jump buttons, blocking problems and notes collapsible) ④ Close & save (enabled when ready). The old upload card, exception cards, provider-links card and bottom close button are gone.
- Group sessions tab: payroll hand entry removed (approve/remove only); compact table — action first, clinician + group + notes in one column, "When" = date · time, cap credit under the code, no horizontal scroll at laptop width.
- Steps v2 (`ppuStepsHtml(R,p,pp,closed)`, shown for open AND closed periods): ① Upload Valant Appointment Documentation CSV ② Verify or correct staff links ③ Review and approve meetings, groups and reimbursements ④ Close the pay period ⑤ Paychex CSV (Download + View report, disabled until closed; `ppuPaychexReport/Csv` refuse while open). Top bar keeps only a "Working preview (CSV)" while open.
- Approval gates closing: every staff-logged meeting & admin entry now saves `approved:false` (payroll-entered and imported rows are approved); pending meetings and pending groups are **blocking** exceptions; training reimbursements are added `approved:false` and need ✓ Approve (`ppuReimbApprove`, `ppuReimbPending`), checked in `ppuClose`. Only approved reimbursements reach Paychex. Meeting tab has "✓ Approve all" (`ppuMtgApproveAll`).

### Office Bookings (My Homebase, Nov 2026)
- Page `offices` (nav under My Homebase, `renderOffices`). Sites/office counts in `OFFICE_SITES` (AMH 9, HAD 11, SOWK/Longmeadow 10, NOHO 4); hours `OFFICE_OPEN`–`OFFICE_CLOSE` (7–20), whole-hour blocks. Office names/notes per site in kv `app_office_rooms` (Admins edit via “⚙ Office names”; default “Office 1..N”).
- Firestore `officeBookings` (`window.officeStore`): {site,room,sid,name,kind:'weekly'|'date',dow,date,until,start,end,status:'pending'|'approved'|'declined',note,skip[],requestedBy/At,decidedBy/At}. Weekly + one-off; `obOn` decides if a booking covers a date; `obConflicts` blocks overlaps with approved bookings (CTM can “Free up this day only” on a weekly booking).
- Therapists: view any site (site tabs → week → day grid of hours × offices), click an open slot or “Request an office” → pending. CTM/CPM of that site (`obCanManage`: Team match + title CTM/CPM) and Admins: “Requests waiting for you”, approve/decline, assign anyone directly (approved), free up a day, remove. Pending requests also appear in My Homebase → Needs your attention for approvers (`homeLoadOfficeReq`).
- My Homebase widget “My office” (`homeOfficeWidgetHtml/homeLoadOfficeWidget`): this week’s approved bookings + pending count.
- Virtual-only staff (profile Format = “Virtual Only”) don’t see the nav item, page or widget (`obShowFor`), unless they manage a site.
- firestore.rules: new `officeBookings` block (read: domain; create: own pending request, or Supervisor+/Admin; update: Supervisor+/Admin; delete: Supervisor+/Admin or own pending). Existing bookings are entered by CTMs by hand (no import).
- Site visibility: `obSitesVisible()` — Admins/Super Admins see every site; therapists, CTMs and CPMs see **only their own Team’s site** (single “🏢 Site offices” header, no site tabs). Staff with no office Team get a message.
- CTM alert: each request shows in the CTM’s My Homebase → Needs your attention (“N office requests to review” with who/when) and a red count badge on the Office Bookings nav item (`obPendingForMe`, `obBadge`). CTMs can also “+ Assign an office” to add anyone to their site’s calendar.
- **Office settings** (Homebase Settings → 🚪 Office settings, `hbmRenderOffices`; Admins / manage-homebase): per site — opening/closing hour, open days, “bookings open at this site” switch (kv `app_office_cfg` {SITE:{open,close,days,on}} via `obCfg`), and the office list (rename, note, reorder, add, remove with upcoming-booking warning; kv `app_office_rooms`). Office Bookings has a “⚙ Office settings” button that links there. Calendar grid, request form and save validation use the site’s hours/days; closed days show “closed”.

### Last wave (Nov 2026)
- **Clinical Profile for Intake** now uses option D tabs: header card (avatar, name, status pill, clinician picker, Save) + `.hb-tabs` (New Client Request · Ages & Modalities · Diagnostic Realms & Exclusions · Identities (optional)); the left rail is gone (the Dx summary sits beside the realms on that tab). New optional **Identities** tab: `IP_DOC.ident={list:[],other:''}` chips from `IP_IDENTS` (LGBTQIA+, race/ethnicity/culture, lived experience, faith & language) + free text; never required; shown as 🌈 chips on Intake Finder cards.
- **Staff alerts have a realm** (`SA_REALMS`: Clinical, Documentation, Billing, Credentialing & licensing, HR, Compliance, Scheduling & office, IT, Other — required). Billing alerts can carry a **Valant client code only** (validated: no spaces, must include a digit), a reason (`SA_BILL_REASONS`) and **⛔ Hard stop** (forces level Critical). Realm tag + client line show on My Homebase, the Employee File flags, the alert modal and Homebase Settings.
- **Bulk Record Upload** (was CEU Uploads; page id still `ceu-upload`, nav moved to Admin Logistics): many files → employee (filename match) + destination (`DOC_SECTIONS`: hiring, license, ceus, review, personnel, comp, other; guessed from filename; “set every unassigned file to…”) + name/date (CEU: title/date/hours). CEU → `_ceus` + staffFiles doc as before; others → `_files` with `section`, `label`. Employee File: Non-Private Docs grouped by section (comp excluded), Credentialing tab lists `license` docs, Comp & Pay tab lists `comp` docs; single upload has a “file into” picker (`docsListHtml`).
- My Homebase news ticker line removed (and the Ticker option on news posts).
- Nov 2026: **Homebase Management renamed Homebase Settings** and moved to the top of Admin Logistics. **Bulk record upload** is now a Homebase Settings section (`HBM.sec='bulk'`, admins; renders `renderCeuUpload` into `#ceu-upload-body` inside the section); the old nav item is hidden and `showPage('ceu-upload')` redirects there.
- **Therapy Thrive** (Clinical Corner, page `therapy-thrive`): coming-soon placeholder via `PLACEHOLDERS`.

### Cleanup Batch 1 (Nov 2026) — see Claude outputs/cleanup/
- Removed ~97 unused functions and 18 hidden pages (old Meeting & Admin Time (HR) page code, old "Payroll Processing (retired)" hand entry, My Therapist Profile, old Employee Profile page, old Alerts / Capacity Data / Suggestion Box pages, Intake Traffic Control and 10 empty stubs). Redirects for old links kept (#meetings-hr, #coderules, #ceu-upload, #clin-howtos).
- Kept on purpose: the Payroll Review *code* (prOpenSheetForPP — the Capacity Dashboard pay-sheet fallback for non-Payroll-Processing periods still uses it; only its page was removed) and the self-running startup helpers `seedSuperAdmins` / `promoteOnboardingToActive` (they run on every load).
- Supply Ordering added to Admin Logistics (admins only); eCANS added to Clinical Corner as coming soon. Employee File (roster view) Credentialing tab now lists credentialing documents and Comp & Benes lists comp documents.
- Verified with Claude outputs/cleanup/sweep.js + flows.js: all 34 remaining pages identical to baseline for 5 role views, 0 JS errors, 13/13 flows pass.
- **Cleanup Batch 2:** removed 217 unused style rules (old capacity cards, old Clinical Profile rail/cards, treatment-profile, old onboarding workflow buttons, old chat widget, etc.; 8 selector lists trimmed) and the unreachable Therapist Profile / Intake Coordinator code block (TP_* constants, renderIntakeCoord). Verified: 68 page screenshots (Super Admin + Therapist) pixel-identical before/after, all 34 pages match Batch 1 for 5 role views, 13/13 flows pass. index.html now ≈1.37 MB (from 1.54 MB before cleanup).
- **Cleanup Batch 3:** removed 131 style declarations that were always overridden (the same selector set the same property again later, or an `!important` rule for that exact selector already set it) and 17 rules left empty by that; static CSS 65 KB → 62 KB, duplicate selector definitions 56 → 38 (the rest set different properties, so they stay as is). Only the main static `<style>` block was touched; CSS injected by page modules (ppuCss, ipCss, …) wasn't. Verified: 68 screenshots identical except emoji anti-aliasing on the Log out button; 34 pages match Batch 2 for 5 role views; 13/13 flows pass.

### Phase 4 wrap-up (Nov 10, 2026)
- firestore.rules: staff can no longer write `kv/tp_*` (retired therapist-profile drafts). Deploy together with the `officeBookings` rules from Office Bookings.
- Added the "Current state" section at the top of this file.

### Suggestion box saves (Nov 10, 2026) — ⚠ rules
- `submitSuggestion` writes to Firestore `suggestions` via `window.suggestStore`. Anonymous (default) saves no name or staff id; otherwise the signed-in person's name (the old pick-any-name list is gone). Super Admins: Homebase Settings → 📬 Suggestions (filter Open/New/Done/All, mark read/done, private note) + “N new suggestions” in Needs your attention (`homeLoadSuggAlert`). New rules block `match /suggestions/{id}` — deploy with the rest.

### Payroll Processing CSV name matching (Nov 2026)
- Meeting & Admin Time upload and the new Training Reimbursement upload match names like Valant provider links: saved link → `ppuMatchStaff` → pick from "Possible matches"/Everyone. Shared helpers `ppuImpNameLookup`, `ppuImpNamesPanel`, `ppuMtgNameLink(key,sid,'m'|'r')`, `ppuImpSaveAuto`.
- Links saved in payrollConfig doc `ppuMtgNames` {map:{normalised name: staff id}}. Unmatched rows don't import until picked.
- Reimbursement upload (`ppuReimbImport*`, `PPU_RIMP`): all rows go into the selected period as unapproved; duplicates and PAID rows start unticked.

### Pay privacy for leaders/non-clinical + Reimbursements tab (Nov 2026)
- `payHideMoney(s)` = non-clinical OR not diff/bonus eligible (`payEligible`, so the Employee File override applies). Those people see hours/headcounts only, no $ except the anniversary bonus: Pay Period Snapshot (`paySnapNoMoney` → `ppuStatementHtml(opt.noMoney)`, `prMtgTable(...,'none')`), Meeting & Admin Time page (`mtgNoMoney`), My Homebase meeting widget. Super Admins viewing someone else's snapshot still see $.
- Their snapshot also: no FFS Hours Paid, no service-type bars, no FFS/differential columns; no-shows read "No Show - Client Charged" / "No Shows - No Charge" (`psNoMoneyHead`); bonus band titled "Bonus" (anniversary only); no Paid Time, Supervision and Meetings band; no unpaid-meetings card.
- Payroll Processing "Training Reimbursement" tab is now **Reimbursements** with categories `REIMB_CATS` (training, license → Paychex Professional Reimbursement; others → Expense Reimbursement; `vendor:true` rows never paid via payroll). `reimbGuessCat` maps the Check Request form's category/type.
- CSV upload reads the Check Request sheet (never reads client name/address columns; "Refund Check to Client" rows skipped). Paid rows → `payrollConfig/reimbHistory` {rows}; unpaid → current period unapproved. Name match also by APP email. History card on the tab merges imported history + closed periods' reimbursements, filter by category/year/person, recategorize/remove imported rows.

### Fix: pay period wouldn't close ("Could not save the snapshot") (Nov 2026)
- Cause: `payrollSnapshots` is create-only. A big period's main snapshot doc (employees + their meeting items) could exceed Firestore's 1 MB limit, and the failed attempt left ledger-part docs behind, so every retry hit "update denied".
- `payStore.createSnapshot` now writes each attempt under its own token (`linePrefix`/`empPrefix`), stores employees+exceptions as JSON text parts, uses `<id>_r<token>` if the main doc already exists, returns the id used, and keeps the reason in `payStore.lastError` (shown in the toast). `getSnapshot` reassembles; the period's `snapshots[].id` is used to load it. Old snapshots still load.

### Capacity Dashboard: hours before hire date warning (Nov 2026)
- `capHoursBeforeHire(s)` = hours credited in pay periods that ended before Date of Hire. When present, the attainment callout is replaced: admins (and anyone viewing someone else) get "Hours credited before hire date — check the Date of Hire or provider link"; the person themself gets a neutral "being double-checked" note instead of the congratulations.

### Capacity changes vs the new-hire ramp (Nov 2026)
- `capRampCheck(s,fromISO,hireRaw)`: a Weekly Capacity change can't start inside the ramp (day after hire → hire+44; full pace from hire+45 = `capRampEnd`). A change dated on/before the hire date = starting capacity (`capSetStartingCapacity`), ramp still applies. Enforced in Capacity adjustments (`capAdjAddChange`) and the Employee File edit (`capEfCollect`).
- Employee File: Date of Hire must parse (saved as MM/DD/YYYY); changing it is blocked if an existing capacity change would land inside the new ramp. `capAdjustNotes` flags any existing change inside the ramp.

### Employee File Weekly Capacity = same timeline as Capacity adjustments (Nov 2026)
- Changing Weekly Capacity on the Employee File now requires choosing when it starts (`ef-capwhen`): hire date (= starting capacity via `capSetStartingCapacity`, ramp applies), this pay period, or a date (ramp guard applies). Live effect line (`capEfEffect`: goal to date and year goal before → after). Biweekly is read-only (2 × weekly). `capEfHistHtml` lists recorded changes + ramp window. Saving clears the goal cache and re-renders the Capacity Dashboard if open.
- Previously the date box silently defaulted to the current pay period, so the YTD goal barely moved — that's why edits "didn't impact the dashboard".

### Rules: effective dates, bulk re-close, workbook UI; one capacity editor (Nov 2026)
- **Effective-dated rule changes:** `rules.changes=[{id,k,old,v,from,at,by,ver}]`; `ppuRulesAt(rules,dateISO)` / `ppuRulesForPP(ppId)` give the rules in effect on a pay period's start (used by compute, groups tab, codes tab and the snapshot). Saving asks "Effective from" (pay period, or "All pay periods" = drops that field's dated history). Version history tab lists dated changes with "Apply to all pay periods" (`crDatedAll`).
- **Bulk re-close** (`PBR`, `ppuBulkOpen/ppuBulkHtml/ppuBulkRun`): Payroll Settings → ↻ Re-close pay periods (also offered after a save, and "Re-close several…" on a closed period). Reopens + recomputes + `ppuClose({silent:true})`; periods with issues/pending/unlinked are left open and reported. Reason required.
- Workbook: Category is a dropdown (+ "New category…") and a category filter; #/Category/Service ID columns and the header are frozen (`.cr-scroll`).
- **Capacity:** Weekly Capacity is changed ONLY in the capacity dialog (`capDlgOpen`) — Employee File Admin actions → Change capacity…, the "📈 Change capacity" link on the profile, the "Change…" button on the (now read-only) edit-form field, and Capacity adjustments. Dated (hire date = starting capacity/ramp, this pay period, or a date after the ramp), live goal effect, recorded changes with Remove; `capRefreshViews` re-renders.

### Group capacity credit = attendees × .33 (Nov 2026)
- Every logged group session with a headcount (any group code): clinical-hours credit = headcount × `settings.groupClinPer` (default 0.33, editable in Payroll Settings → Differentials & Bonuses, dated like other settings). Pay is unchanged (headcount × groupRate). Other group codes still use their workbook row.

### Group share on capacity dashboards (Nov 2026)
- The "Group Clinical Hours" widgets read `GROUP_CREDIT_DATA` (kv/app_group_credit, per year) = each person's group-session credit per pay period, written by `ppuWriteCapacity` from `E.grpClin` (logged groups: attendees × .33; Valant rows with a group-session code: any 90853 or per-participant code — `ppuIsGroupSession`). It's already inside CLINICAL_HOURS_DATA, so `capRealHours` moves it from individual to group (total unchanged). Legacy GROUP_HOURS_DATA (raw × 0.333) still adds. Populated when a period closes → re-close earlier periods to fill history.

### Staff roles & titles editor; missing-info detail (Nov 12 2026)
- Homebase Settings → Roles & permissions → **Staff roles & titles** (`rtHtml`, ADMIN_TAB 'rt'): add / rename / delete roles (CONFIG.roleOpts) and job titles (CONFIG.jobTitleOpts). Rename/merge or delete migrates every staff record (`rtMigrate`); delete asks where to move people. Locked roles used by code: `RT_LOCKED`. Saved to kv/app_config with `removedRoleOpts` / `removedJobTitleOpts` so deleted built-ins aren't re-added by `cfgApply`.
- Deleting a custom access role (`permDel`) now asks where to move its people (another custom role or built-in access).
- Employee profile "Alerts & flags": the missing chip lists the fields ("❗ Missing: Email, Phone, … +N more") and opens the fill-in list (`showMissPopover`).

### Payroll Processing fixes (Nov 12 2026)
- Step 3 lists every blocking problem with direct buttons (`ppuProblemsHtml`): Open it → (`ppuGoLine` jumps to and highlights the appointment row `#ppu-L-<key>`), Change code…, Not a duplicate, Exclude…, Fix in Payroll Settings → (`ppuGoRule` opens the workbook searched to that code), or the Groups/Meetings tab / step-2 links.
- Meeting & Admin Time entries are only PAID when their period closes. `ppuMtgInPP(m,pp)` decides membership (unpaid & unclaimed or claimed by this period; PAID only in its period). Opening an open/reopened period runs `ppuMtgUnpayOpen` (PAID→UNPAID for entries tied to it) so they stay editable; the CSV import no longer marks PAID (keeps `csvStatus`/`csvPayDate`) and ties rows to the period via `paidPeriod`. `ppuMtgEdit` blocks only entries paid in another period.
- Closing shows a full-screen spinner with step text (`ppuBusy`).
- 'Screening' added to `PPU_HEADS` (its own column) — it used to raise a "No display column" note (e.g. Judge, Anjali).

### Report Center (Nov 12 2026)
- `renderReportCenter` (RC state). Super Admin: per pay period, reads the Valant rows (`payStore.rows`) and re-runs `ppuCompute` with `ppuRulesForPP`, the period's corrections, current links and logged groups → cached counted lines {sid, date, st, en, tx, cat, head, del, fac, clin} (`rcLoadPP`). Admins: hours from CLINICAL_HOURS_DATA (no code filters, no Office Utilization).
- Dates: presets `RC_PRESETS` (this/last pay period, MTD, last month, QTD, last quarter, YTD, last 30/90 days, custom) via `rcDates()`; `rcRange()` = pay periods overlapping; lines filtered by date; goals by exact dates (`rcGoalBetween`); chart buckets by pay period / month / week (`rcBuckets`).
- **Clinical Hours Analysis:** filters (dates, site/Team, role, format, title, staff status, category, code, delivery); KPIs; hours vs goal per pay period (SVG bars + dashed goal); hours vs goal by site; breakdown by site / license level / format / title / tier / clinician (CSV); hours by code / category / heading. Goal = `capGoalBetween` per person per period.
- **Office Utilization:** approved bookings (`obOn`) vs in-person sessions by the booked clinician at that site overlapping the booked hours; KPIs, by site, weekday×hour heatmap, by office, by clinician; in-person sessions with no booking; virtual hours inside booked slots. Valant FacilityID → site map guessed (`rcFacSite`) and editable, saved in kv/app_rc_facmap.

### Report Center additions; Homebase logo; welcome + tour (Nov 12 2026)
- Report Center → **Sessions & Peak Times** (`rcSessionsHtml`): all counted appointments (in person + virtual) by home site + entire practice (CSV), stacked in-person/virtual bars, where in-person sessions happened (by facility), peak start-hour line chart (`rcLineHours`), sessions by weekday.
- Office Utilization → **Office grid** (`rcRoomGrid`): one row per office, one column per hour, cell = used/booked hours, weekday filter (`RC.ou.dow`).
- Brand: public/homebase-logo.png (wordmark cropped from the brand kit, used as is), favicon.png (180, house mark), favicon-32.png, favicon.ico. `LOGO_SRC`/`HB_LOGO_SRC` = /homebase-logo.png. Sidebar shows the logo on a white tile; sign-in card shows it. Title "Homebase — Let's Work Together".
- **Welcome** after sign-in (`hbWelcomeMaybe` from the auth module, once per browser session; "Don't show this" = localStorage hb_welcome_off): logo + tagline, "Take the tour" / "Continue to site".
- **Tour** (`hbTourStart`, `HB_TOUR_STEPS`): spotlights the sidebar items the person can see, Next/Back/Skip, arrows/Esc; positions divide by the body zoom (1.35). "🧭 Take the tour" under the logo.
- **Clinician walkthrough** (`HB_TT_STEPS`, `hbTTStart/hbTTShow/hbTTDraw`): for therapists/supervisors (and clinicians in other views except admin roles) "Take the tour" runs a chaptered, page-by-page walkthrough — Welcome → start page widgets → Meeting & Admin Time form → Capacity Dashboard → Office Bookings → Clinical Profile for Intake → Pay Period Snapshot → Employee File / policies → done. It navigates pages, waits for each target, spotlights it, glows the menu item (`.nav-item.hbt-on`), shows chapter progress; missing targets are skipped; ends back on My Homebase. Admin roles get the menu tour (`hbTourStart('menu')` forces it).

### Team (site) history (Nov 15 2026)
- `staff._teamHist=[{from:'YYYY-MM-DD'|'',team}]`; `staffTeamHist`, `staffTeamAt(s,iso)`, `staffTeamSegments(s,a,z)`, `staffTeamRecordMove`. Changing Team on the Employee File edit form requires "Date they moved to the new team" (`ef-teamfrom`, blocked if a later move exists). Profile shows the history + "🗓 Team history" dialog (`teamHistOpen`, also in Admin actions) to add / change / remove moves.
- Report Center uses the team on each date: site filter, hours & goal by site (goal split across team segments), breakdown by site, Sessions & Peak Times by site. Capacity Dashboard / other pages still group by current Team.

### Office Utilization overhaul — live + retained history (Nov 15 2026)
- `rcOfficeHtml` rewritten. **Live** card (`rcOfficeLive`): per site, offices in use right now, today's booked vs available hours, today's office×hour grid with names.
- **History** (`OFH`, `ofhBackfill`): every past day is frozen into kv `app_office_hist_YYYY_MM` {days:{iso:{at,sites:{SITE:{open,close,openDay,rooms,occ:[{id,room,sid,name,start,end,kind}]}}}}} on an Admin's visit to Report Center or Office Bookings (backfills all missing days from the first approved booking to yesterday; kv write = admins). Reports read saved days, live for today/unsaved.
- Measures: occupancy = booked ÷ available office-hours (offices × open hours on open days); weekly occupancy lines per site (`rcOccLines`); by site; office×hour occupancy grid (`rcRoomGrid`, weekday filter); weekday×hour occupancy heat (`rcHeat`); by office; by clinician; CSV of the full booking record. Super Admin adds Valant "used" hours, virtual-in-slot, in-person with no booking.
- Bookings keep history: `obRemove` ENDS a started weekly booking (until = yesterday, endedBy/endedAt) instead of deleting; past one-offs can't be removed; only not-yet-started bookings are deleted.

## Events: picture, RSVP and RSVP reminders (Nov 15 2026)
- Event modal (`hcalEdit`) has `hcalEditExtrasHtml`: picture/flyer upload (PNG/JPG/GIF/WebP ≤5 MB → Storage
  `refLibrary/{eventId}/{file}`, saved on the event as `img:{path,url,name}`; no storage rule change) and
  "Ask people to RSVP" → `rsvp:{on,by,maybe,guests,alert,alertFrom}`.
- Answers: Firestore `eventRsvps/{eid}__{sid}` via `window.rsvpStore` (mine/forEvent/set/remove). Each person writes
  only their own; Admins read all. **Needs a firestore.rules deploy.**
- `hcalRsvpHtml` (buttons on the calendar card), `homeLoadRsvpAlerts` (💌 reminder in Needs your attention for invited,
  unanswered people from alertFrom to the RSVP-by date), `hcalRsvpAdminLine` / `hcalRsvpList` / `hcalRsvpCsv` (admin counts,
  names by answer + no reply, CSV). Invited = active staff, practice-wide or the event's team.
- Capacity chart: month labels (`monthAxis`) under the plot; chart height 366, padB 84.

## Report Center chart labels (Nov 15 2026)
- `rcBarsTime` shows a second label line (`p.sub`): pay-period dates (1/5–1/18) and week dates; weeks are labelled
  "Wk of M/D"; months show the year on the first bar and January. Hours value above each bar when there's room.

## Legal name / preferred name / pronouns (Nov 15 2026)
- Roster fields 'Legal Name', 'Preferred Name', 'Pronouns' (editor: ef-legal / ef-pref / ef-pron, replacing ef-name).
- 'Clinician' stays the DISPLAY name used by every screen, report, dashboard and document: `staffApplyNames(p)` sets it to
  Preferred Name, else Legal Name, on save, and carries a rename into other people's 'Supervisor' / 'Reports To' (stored as names).
- Name matching (capImpMatch, findSimilarStaff, ppu Valant provider match, prSuggestSid, super-admin seed, add-employee dupe check)
  checks both names via `staffNameKeys(s)`. Legal name shows only on the profile (admins) and in roster search.
- Pronouns: `staffPronounTag(s)` beside the name on the profile header and roster; "Pronouns" row on the profile.
- Existing records: Legal Name is blank until someone saves the profile (the editor pre-fills it from the current name).

## My Homebase layout + Locations (Nov 15 2026)
- Home: Row 1 = site & emergency | Needs your attention + Latest Practice News (news moved up). Row 2 = `homeCapRowHtml()`:
  wide capacity card (`hs-capwide`, extra detail from `homeCapMoreHtml`: year to date vs expected, ahead/behind, weekly goal,
  group credit, catch-up pace, the four benchmarks) beside Clinical Profile for Intake + My office. Row 3 calendar, Row 4 suggestion box.
  Meeting & admin time widget removed from the homepage (and from the therapist tour); the Meetings page is unchanged.
- Homebase Settings → 📍 Locations (`hbmRenderLocations`, `locEdit`, `locSave`, `locClose`/`locCloseCommit`, `locReopen`).
  Data = CONFIG.siteDirectory[code] {l, addr, phone, police, fire, offices, closed, closedNote} + teamLabels/siteMeta/siteOrder/teamOpts,
  saved to kv/app_config by `locSaveConfig`. Code is fixed (it's the staff Team code and the booking site code).
- `OFFICE_SITES` is now a getter: open locations with offices (room count from kv/app_office_rooms, else `offices`, else defaults).
  `officeSitesAll()` includes closed ones — Report Center uses it so history stays. New location with N offices creates rooms
  "Office 1..N". Closing (from a date) ends weekly bookings the day before, declines later one-time ones, hides it from pickers
  (`locOpenCodes`, `siteIsOpen`). Team pill colours for new codes come from `locApplyCss()`. Weather only for built-in sites (SITE_NWS).

## Intake profile realms, Back button, Roles & permissions retool (Nov 15 2026)
- Diagnostic Realms & Exclusions: rows are `.ip-lvrow` with one segmented control `.ip-lv` (Low / Moderate / High / Prefer not;
  brand colours). Identity items simply have no "Prefer not" (blank slot keeps columns aligned) — no "can't be declined" label.
  "Your selections" (High / Low / Prefer not) is a strip of chips above the list instead of a third column.
- Topbar Back button `#hb-back` ("← <previous page>"): `HB_BACK` stack, `hbBackTrack` (called in showPage), `hbGoBack`, `hbBackPaint`.
- Roles & permissions (Homebase Settings → Roles & permissions, first sub-tab): one list of built-in levels + custom roles
  (`renderPermBuilder`, `permEditorHtml`). Super Admins can rename built-in levels and change their description/colour
  (PERM.names in kv/app_perm_roles, applied to ROLES by `permApplyNames`; originals in ROLES_ORIG), edit pages/abilities
  (not Super Admin, which sees everything), and add people to a level (`permSaveLevel` sets ROLE_MAP + persistRoles).
  "Reset" restores name + page access. Sub-tabs: Roles & permissions · Who has which level · Staff roles & titles.
- Capacity ring (Nov 15): 112px, thin 5.5 stroke, navy % + 'of goal'; a faint inner arc shows how far over 100%.
- Homebase Settings (Nov 15): sections are a grouped side nav (`hbmShell` → .hbm-layout/.hbm-nav/.hbm-nl, `hbmGoSec`) instead of top tabs. Container class is .hbm-content (.hbm-main is the row text class).
- Office Utilization simplified (Nov 15): `rcOfficeHtml` = toggle chips (Dates presets + from/to, Site, Days, Show Booked/Used [SA]) → 4 KPI tiles → ONE office×hour grid (all sites grouped, row + site totals) + CSV + collapsed Valant location mapping (SA). Weekday chip now filters everything. Old live/weekly/heat/tables helpers (rcOfficeLive, rcOccLines, rcRoomGrid, rcHeat) are unused but kept.
- Office grid header (Nov 15): big site name + tags for date preset/range, day filter and Booked/Used (.ou-big/.ou-tags).
- Office grid booked + used together (Nov 15): each cell (roomHeat {a open days, b booked, k booked on days with Valant data,
  u used}) is filled green (used) / red (booked, no in-person session) / teal (booked, no Valant data yet) in proportion,
  stronger colour = booked more often; number = % of open days booked. Used % = used ÷ booked on data days (T.bkd).
- Recommendations (`rcOfficeRecs`): weekly bookings to Free up (<25%) / Review (<50%) from past occurrences with Valant data
  (≥4; last 4 weeks count double; used = booked person had an overlapping in-person session at that site), ranked by empty
  hrs/week, with "End booking…" (`rcRecEnd`, sets until=yesterday). Plus offices booked <15% of open hours (≥4 weeks), grouped by site.

## Recruitment overhaul — step 1: new application form (Nov 15 2026) ⚠ rules + functions
- `public/apply.html` rebuilt from scratch: 7-step form (Before you start [client gate, staff connection] → About you →
  Position & licensure [Psychotherapist I/II cards, `POSITIONS`; license auto-suggests position; pre-licensed asks expected
  licensure + supervision] → Schedule & location → Clinical focus → In your words → Resume & submit [required resume,
  optional cover letter, summary, consent]). Brand colours, mobile-friendly, honeypot + 8-second guard.
- Writes one flat, readable doc to `applications` ('_v':2, '_token', '_resume'/'_cover' {path,name,size,type}); ≤51 keys
  (rule limit 60). Files → Storage `applications/{36-hex token}/(resume|cover)_<name>` (PDF/Word, 10 MB, public create,
  Admin read/delete). **storage.rules + firestore.rules changed → deploy storage and firestore:rules.**
- Recruitment inbox shows Position + "📄 resume" and Open resume / Open cover letter buttons (`appsOpenFile`); `_` keys hidden.
- Admins see "N new applications to review" in Needs your attention (`homeLoadAppsAlert`, `#home-appsalert`).
- Confirmation email: Cloud Function `applicationReceived` (functions/index.js) adds a `mail` doc for the Firebase
  **Trigger Email** extension (must be installed with SMTP for hr@). `firebase-admin` added to functions/package.json →
  `cd functions && npm install`, then `firebase deploy --only functions`. Clients can't touch `mail` (no rule).

## Report Center loading speed (Nov 15 2026)
- `rcLoadPP` saves each pay period's counted lines as one summary doc `payrollConfig/rcLines_<pp>` {sig,at,n,data (packed JSON, `RC_PACK`)}
  and reuses it while the fingerprint `rcSig` matches (upload id/chunks, status, snapshot count, closedAt, corrections, manual groups,
  rules in effect `ppuRulesForPP`, provider links `RC._linkSig`, logged group meetings in the period). Anything changes → recomputed
  and re-saved. `rcEnsure` loads up to 6 periods in parallel. Super Admin only (payrollConfig rules) — no rules change. No client names.
- ⚠ storage.rules: `firestore.get()` doesn't work in this project's Storage rules, so `isAdmin()` there = only the hardcoded
  accounts in `isBootstrap()` (will@, michael@, comms@). Applicant resumes (applications/…) open only for those accounts until
  roles move to auth custom claims. (Nov 15: restored Will's Nov 12 storage.rules after it was overwritten by a stale copy.)

## Report Center: chip filters everywhere, chart headers, Workforce Analysis (Nov 15 2026)
- Shared filter UI (office-utilization style): `rcChipRow(label,key,opts,cur,fnName,allLabel,max)` (pill buttons, "+N more"),
  `rcDateRow()` (date presets + from/to), `rcFilterBar('hours'|'sessions')` (Dates, Site, Role, Format, Title, Staff,
  Category, Code, Delivery; `rcFSet`). Every chart card starts with `rcHead(eyebrow,title,tags,right)`; `rcTags()` lists the
  active filters. Breakdown / service "group by" and pay period / month / week switches are chips too.
- Clinical hours bar chart: axis titles ("Clinical hours", "→ Pay period (dates under each bar)" / week / month),
  value above each bar, dates under each label.
- New tab **👥 Workforce Analysis** (`rcWorkforceHtml`, Admins; no pay data). State `WF` (own dates `wfDates`: This year,
  Last 12 months, Last year, This quarter, Last 90 days, All time, custom). Filters: team (team on the date of each event via
  Team history), clinical/non-clinical, title, role, format, employment type (Capacity Tier), license. Headcount on a date =
  hired on/before and Term Date not passed (former staff without a Term Date are excluded + noted). KPIs: headcount (clinical/
  non), net change, hires, separations (≤90-day early leavers), turnover = seps ÷ avg(start,end) (+ annualized pace), retention,
  average tenure, on leave/onboarding/offboarding. Monthly trend SVG (`wfTrendSvg`), breakdown table by any dimension (CSV
  `wfCsv`), tenure bands, composition, new hires + separations lists, coming up in 60 days (anniversaries, last days, licenses).

## Clinical Policies → PDF sign-offs (Nov 15 2026) ⚠ rules + storage + bucket CORS
- Clinical Policies & How-To Manuals page tabs: **📜 Clinical Policies** (new, `LIB_CAT='pol'`, `polRender`) · Clinical How-To Manual ·
  (Super Admin only) "Clinical Policies Manual (old)" = the old book + sign-off rounds, kept read-only for history.
- Data: Firestore `policies/{pid}` {title, cat (POL_CATS), desc, aud (hbmAudMatches shape), status active|retired,
  versions:[{v,path,name,size,sha (SHA-256 of the PDF),at,by,notes,due}]} — all staff read, Super Admin write.
  `policySigs/{pid}_v{n}_{sid}` create-only {pid,v,sid,email (auth),name (typed),legal,statement,sha,title,file,openedAt,ua,at=server time}
  — only the signer can create (rules check id, sid, email, request.time); only signedPath/signedKind/signedAt can be added later; no delete.
  Storage: `policies/{pid}/v{n}/{file}` (immutable, Admin create, all staff read), `policySigned/{email}/{pid}_v{n}.pdf` (signer writes once).
- Signing (`polDocHtml`, `polSign`): PDF in an iframe; checkbox + typed name unlock 4 s after the PDF loads (or "Open in a new tab");
  mismatch with the legal name asks to confirm. Signed copy = original PDF + signature certificate page (`polMakeSignedPdf`, pdf-lib
  1.17.1 from cdnjs, loaded on demand); falls back to certificate-only if the PDF can't be fetched (bucket CORS — see storage-cors.json;
  `gsutil cors set storage-cors.json gs://advance-intranet.firebasestorage.app`). `polDownloadSigned` regenerates it if missing.
- Assignment: audience + version due date; people hired after a version was published are due hire + 14 days (`polDue`).
  New version (`polNewVersion`, "what changed" required) → everyone assigned signs again (status 'update'); old signatures kept.
- Alerts: pinned (data-crit=1) "Please sign / Overdue" items in Needs your attention (`homeLoadPolicyAlerts`, `#home-policyalerts`)
  + red count badge on the nav item (`polBadge`). Admin (`polAdminHtml`, `polAdminDetail`): % signed per policy, by-person table,
  per-policy status chips, signed copies, version history with fingerprints, audit CSV (`polCsv`), retire/restore.

## Insurance Catalogue + Projected Revenue (Nov 15 2026) — Super Admin only
- Homebase Settings → Billing & payroll → 🏥 **Insurance Catalogue** (in progress; `insRender`, `INS`): CPT code table (code, service,
  average reimbursement) seeded with APP's averages (`INS_SEED`: 90791 140.68, 90832 58.87, 90834 88.53, 90837 120.13, 90839 113.30,
  90840 55.78, 90846 82.43, 90847 86.08, 90882 71.80, 90887 59.40, 90853 32.14), plus payer columns with known rates and their average
  ("use as average"). Saved to `payrollConfig/insCatalog` (Super Admin rules; no change). This is practice revenue, not clinician pay.
- Report Center → 💲 **Projected Revenue** (`rcRevHtml`, tab only for Super Admins): counted Valant lines × catalogue average by CPT
  (`insCptOf` takes the 5-digit 9xxxx code; logged groups = attendees × 90853 rate). KPIs: estimated revenue, per week (weeks with data),
  per appointment, per clinical hour, projection (avg weekly revenue over the last 8 weeks with data × weeks to the horizon — year end /
  3 / 12 months; `RC.revH`), actual + projection, capacity-goal potential (goal hours × revenue per clinical hour). Monthly chart
  (`insRevSvg`), by CPT (CSV `insRevCsv`, unrated codes listed), by site, top clinicians. Uses the same chip filters as Clinical Hours.
- Report Center filter bar: the Role row was removed at Michael's request (Nov 15); Workforce Analysis keeps its own Role filter.
- Event attachments (Nov 15): `event.files=[{path,name,size,type}]` (≤10 per event, ≤20 MB each; PDF/Office/images/txt) in Storage refLibrary/{eventId}/att_<time>_<name>; modal section (`hcalAttPick/hcalAttRemove/hcalAttCommit`), chips on the calendar card and Settings → Events (`hcalAttLinks`, `hcalAttOpen`); deleted with the event. Upload needs a Storage-admin account (isBootstrap).

## Self-service demographics (Nov 15 2026)
- New ability `edit-own-profile` in PERM_CAPS (Roles & permissions → edit a level/role → "Edit their own profile (demographics only)";
  off by default). When on, the person's own Employee File shows "✏️ Update my information" (`selfEditAllowed`, `selfEditOpen`,
  `selfEditSave`) for SELF_FIELDS only: Legal Name, Preferred Name, Pronouns, DOB, Address, Personal Phone, Personal Email,
  Emergency Contact Name/Relationship/Phone. Display name ('Clinician') follows preferred/legal name; supervisors (named in others'
  Supervisor/Reports To) can't change their preferred name themselves. Admins keep the full editor (now also has the personal +
  emergency contact fields). New private fields are in PRIVATE_FIELDS → staffPrivate (self + admins).
- Server: staff/staffPrivate rules already let people write their own record, so this is a UI permission like the others.
- Employee File "Demographic & Employment" tab (Nov 16, Michael picked Option A "simple list"): `pfDemoHtml` — sections with a
  header bar (Contact · Personal · Emergency contact · Job · Capacity), label → value rows (`pfF`, `pfM` shows red "Missing" to
  admins), two columns of rows on wide screens (.pa-*). Contact = APP email ('Email Address'), APP Google Voice ('Google Number'),
  Alternate email, Alternate phone. Emergency contact = name, relationship, phone, alternate phone ('Emergency Contact Alt Phone'),
  email ('Emergency Contact Email'). DOB/address/emergency/alternates are private (self + admins).

## Private Docs in the Employee File (Nov 16 2026) ⚠ rules + storage
- Tab "🔒 Private Docs" (`privDocsLoad`, `privDocsHtml`, `privDocsUpload`, `privDocsOpen`, `privDocsDel`) — only for a real Super Admin
  (`isSuperAdminView()` and role superadmin; not custom roles, not the employee, not on your own record).
- Metadata in Firestore `privateDocs/{id}` {sid,name,cat (PRIV_CATS),date,notes,path,size,type,by,at} — read/write isSuperAdmin() only;
  never on the staff record (which all staff can read). Bytes in Storage `privateDocs/{sid}/{fileId}/{name}` — `isSuperStorage()`
  = will@ and michael@ only (comms@ deliberately excluded). Delete is permanent (confirm).

## Clinical Profile: Client Identities split out + side rail (Nov 16 2026)
- "Populations & Circumstances" is split. **Client Identities** step (`IP_CLIENT_IDS`: LGBTQ+, Transgender / Nonbinary, Gender
  Identity Exploration, BIPOC, Neurodivergent Adults, Religious / Spiritual) uses its own scale `IP_ID_LEVELS`: Affirming (stored "",
  everyone's baseline) · Experienced ("exp") · Specialty focus ("sf"); never declined. Values stay in IP_DOC.pop / IP_DOC.dx
  (`ipIdGroup`), so old profiles carry over (old Low → Affirming, old High → Experienced, via `ipNormMarks`). `ipMarked` skips
  identities; `ipIdMarked(doc,v)` lists them.
- **Life Circumstances & Special Populations** step (`ipCircHtml`): the rest of IP_POPS, grouped by `IP_CIRC_GROUPS` (Life stage &
  family · Occupation & service · Legal & forensic · Safety & acuity; anything new falls into "Other"), Low/Moderate/High/Prefer not.
  Diagnostic Realms no longer lists a Populations realm (`ipRealms` = IP_DX keys; identities filtered out of realm items).
- Every rating list starts with level descriptions (`ipLvLegend`, `IP_LV_DESC`); rows via `ipLvRow`.
- Intake Finder: identity concern → Specialty focus +4 ("★ Specialty focus"), Experienced +2; details list both.
- Layout (Michael picked "Layout 2"): top tabs replaced by a left rail (`.ip-layout`/`.ip-rail`): navy **New Client Request** panel
  with Yes / Not now (`ipReqSwitch` sets status, opens the full request screen — unchanged `ipRequestHtml` — flashes it and shows a
  "You switched… Confirm request" banner while unsaved; `ipReqConfirm` → `ipConfirm`), then numbered steps with a progress bar
  (Ages & Modalities · Client Identities · Life Circumstances · Diagnostic Realms · Your Identities (optional)). Tab keys: req, ages,
  cid, circ, spec, ident. No rules change.
- Nov 16: **New Client Request streamlined** (`ipRequestHtml`, CSS `.ip-req2`/`.ip-rsec`): white card, title + status pill, slim
  90-day goal line, three numbered sections (1 Openings: how many + offices · 2 Who you'd like: client-type chips (`.ip-pchip`,
  hidden checkbox) + note for Intake · 3 When you're open: hours grid + another site). Taking / Not taking is set from the navy rail
  panel (in-page buttons only show when it was never answered). Colour legend dropped (brushes are tinted); stale/never stamp slimmed.
- Nov 16: **"Other" items** on Client Identities, Life Circumstances and Diagnostic Realms (`ipOtherHtml(k)`, `ipOthAdd/Set/Del`,
  `ipOthNorm`, `ipOthList`): `IP_DOC.other={cid:[{n,v}],circ:[...],dx:[...]}` (≤12 each, name ≤80 chars), same level values as
  the built-in lists. Shown on Intake Finder card details ("Other"); not used for matching/scoring. Your Identities already had
  its "Anything else" box.
- Nov 16: **Office picker removed from New Client Request.** In-person hours on the main grid = the clinician's home site
  (`ipHomeSite(sid)` = their Team code when it's a site). `ipSave` writes `offices=[home]`; Intake Finder (`ifLoad`) fills empty
  `offices` from the home site. Other sites still go through "Another site" (extraSites) at the bottom.
- Nov 16: **Alternate email + Alternate phone are required profile fields** (`requiredProfileFields` with `private:true`; `cfgApply`
  adds them to an older saved list). `fieldApplies` only flags private fields when the viewer is an admin or the person themself
  (staffPrivate isn't loaded for anyone else). Employee File shows them as red "Missing" to admins (`pfM`).
- Nov 16: **Employee File edit form mirrors the view** (`buildRosterEditForm`): sections Contact · Personal · Emergency contact · Job ·
  Capacity (same order + labels as `pfDemoHtml`), then Licensure / Credentialing (marked "On the Credentialing tab"). Section headers
  use the view's `.pa-h` bar (`.ef-h`); field labels sentence case. Field ids/keys unchanged, so saveEdit is untouched.
- Nov 16: **Capacity dialog ↔ Employee File edit form.** If the edit form is open for that person with a different Date of Hire typed
  in, `capDlgOpen` uses it (`capDlgPendingHire`, `CAPDLG.hire`, `capDlgView` = record copy with the new date) and shows a note;
  `capDlgSave` writes the new hire date to the record together with the capacity change. `capEfSyncAfterDlg` then updates the open
  form (weekly, biweekly, hire date, capacity history `[data-caphist]`) so its Save doesn't send old values back.
- Nov 16: **Comp & Benes editing + checklist moved** ⚠ firestore.rules. Comp & Benes tab has "✏️ Edit / ＋ Add comp & benefits"
  (Super Admins; also Admin actions → Edit comp & benefits…): `compEditOpen` / `compEditSave`, fields `COMP_FIELDS` (rate2026, pay2025,
  inc2025, incdate2026, incnotes2026, compNotes; med, den, vis, benNotes) saved into kv `app_comp_data` [id] (Super Admin–only, unchanged).
  Date of hire shown there comes from the Employee File. **Compliance checklist** (handbook + HIPAA, `compChecklistHtml`) now sits at the
  top of the Non-Private Docs tab (admins); missing-item clicks go there. Rules: kv `app_comp_checklist` read/write moved from Super Admin
  to Admin (no pay data in it).
- Nov 16: **Benefits & premiums** (Homebase Settings → Billing & payroll → 🩺, Super Admins; `benRender`, `BEN`, `benSave`):
  `payrollConfig/benefitPlans` = {types:[{k,l}] (Medical/Dental/Vision + any added), plans:[{id,type,name,prem:{ee,es,ec,fam} monthly,
  notes}], share:{type:{full:%,part:%,basis:'plan'|'ee'}}, history}. Admin actions menu has ONE "Comp & Benes" item (edit button is on the tab).
  Comp editor enrollment per type (`compBenEditHtml`/`compBenRead`/`compBenSync`): plan | Waived, coverage tier, **start date**,
  **expected end date** → `COMP_DATA[id].ben={type:{plan,tier,start,end}}`, `benGroup` ''(auto from Capacity Tier: FULL/SAL full,
  PART/FRAC part)|'full'|'part'. Costs via `benCost` (premium × APP %, employee pays the rest). Comp & Benes tab table
  (`compBenViewHtml`): plan, coverage, dates ("Ends …" amber / ended rows faded and left out of the current total), premium, APP, employee;
  old sheet med/den/vis amounts still show when no enrollment is set. No rules change (payrollConfig + app_comp_data are Super Admin).
- Nov 16: **Intake Finder → Intake Birdseye** (page id still `intake-finder`; `renderIntakeFinder`). Side tabs (`IF_TAB`, `ifTab`):
  🎯 Match a client (`ifMatchTab`: compact client panel — who, needs typeahead over diagnoses/identities/circumstances/modalities, format+site,
  When grid and "Prefers a therapist who is…" (`IF.tid`, from therapists' own identities, +2.5 boost, never excludes) in collapsibles —
  then ranked cards + "Ruled out"), 🗺️ Openings by team (`ifTeamsTab`: KPIs + per-team table of who's taking, spots, virtual/in-person hrs,
  ages, freshness; not-taking collapsed), 🗓️ Openings calendar (`ifCalTab`: day × hour counts, format filter `IF_CALFMT`, click an hour →
  who's open `IF_CALSEL`), ⚠️ Profiles to update (`ifStaleTab`). Team chips (`IF.team`) filter every tab. Every name shows capacity
  attainment (`ifAtt`/`ifName`, cached in `IF_ATT`, colour = capStatusColor). Taking = status open; stale requests are flagged, not hidden.
- Nov 16 (pass 2): **Intake Birdseye restyle** — one stylesheet `ifbCss` (.ifb-*; old .if-* card/chip styles no longer used on this page).
  Rail with section title + counts + refresh/loaded time; one toolbar (team chips + attainment key "% next to a name = capacity attainment
  (year to date)" with 100%+/90–99%/<90% sample pills); each tab has a title + one-line description. Match: "The client" panel as label |
  controls rows (Who · Needs help with · Format/site), Days & times and therapist-identity preference as ＋ expanders; result cards
  (`ifCardHtml(row,ev,rank)`): rank, name + attainment, title · team · freshness, status pill (N spots / Not taking), reason tags, open hours,
  their note, shared identities, "Full profile". Team tables put "Sees …" under the name; column header "Clinician · attainment".

## Nov 16 batch: license pings, Office Utilization filters, Attainment Tracking, Leadership Dashboard archived
- **License update** (Employee File → Admin actions → Licensure → 🪪 Update license…; `licUpdOpen`/`licUpdSave`): license type, #, effective
  and expiration dates (writes License, License #, Lic Eff Date, Lic Exp Date + License Expiration), what changed, note; pings everyone holding the
  **Credentialing** role (new in CONFIG.roleOpts) and/or **Marketing** role (`licRecipients`) with a staffAlert (realm credentialing, kind license,
  level important) in their Needs your attention. Missing role → the dialog says so.
- **Office Utilization filters**: one row — date chips (This month/Last month/This quarter/YTD/Custom… shows date boxes) + Site and Day dropdowns.
- **Report Center → 🎯 Attainment Tracking** (tab key still `hours`; `rcAttainHtml`, `RCA` state, `rcaRows`, `rcaChanges`, `rcaCsv`): year-to-date
  attainment from capCompute — 5 tiles (attainment, hrs to catch up, under 90%, tier reviews, intake mismatches), site leaderboard (tdSiteStats;
  click = focus that site), clinician table (attainment + hrs, catch-up next 90 days, Intake request status/spots/new-client hrs from IF_DATA,
  checks: tier review, behind & not taking / no profile / new-client hrs below catch-up need / no spots, stale request, ahead & asking for more;
  views Everyone/Under 90%/Needs attention/Intake mismatch/Tier review; sort; CSV), capacity changes this year (_capHist), then the former Clinical
  Hours Analysis (`rcHoursHtml`) under "Clinical hours detail".
- **Leadership Dashboard archived**: nav hidden; `showPage('team-dashboard')` redirects to Report Center › Attainment Tracking. Its code
  (renderTeamDashboard, td*) is kept — tdSiteStats/tdTile are reused.
- Nov 16: **Documents & sign-offs moved to Homebase Settings** (Records → ✍️ Documents & sign-offs, Super Admins; `polSettingsRender` renders
  `polAdminHtml`, category filter chips `POL.catF`; `polRerender` refreshes settings or the library page). Same POL framework (versions, sign by,
  audience, pinned alerts, signed PDF copies, audit CSV). New: categories `POL_CATS` (Clinical policy, Employee Handbook, HR & employment,
  Compliance & privacy, Safety, Forms & agreements, Other) — clinical/safety show on Clinical Policies (`pol`), the rest on the Employee Handbook
  page's new first tab **Handbook & HR documents** (LIB_CAT `hpol`; `polPageOf`, `POL_CAT_PAGE`); **Signature required** toggle (`p.sign===false`
  = reference only: no sign-off, no alerts). Alerts/badges per page (`polMyTodo(page)`; badges on Clinical Policies and Employee Handbook nav).
  Staff pages show "⚙ Manage in Homebase Settings" for Super Admins (`polManage`, `polManageOne`). The old handbook book stays as the second tab.
- Nov 16: **Your Identities list**: added "Jewish" (Race, ethnicity & culture); removed "Faith-informed / religious practice" (group is now
  "Language"); new **Other** group — therapists add their own identities as chips (`ipIdentAdd`, ≤10, stored in ident.list; `ipIdentBuiltIn`
  tells custom from built-in). Older free-text `ident.other` shows as a removable chip there; an old "Faith-informed" pick shows under Other.
- Nov 16: **PDF reader for documents to sign** (`polAfterRender`, `polLayout`, `polRenderPage`, `polZoom`, `polScroll`, `POLR`): PDF.js 3.11.174
  (cdnjs, loaded on demand by `polPdfJs`) draws pages fit-to-width on canvases (lazy via IntersectionObserver), − / Fit / + zoom, "Page x of N".
  Signing unlocks only when the reader reaches the end of the last page; the signature records readToEnd, pages, readEndAt (policySigs stays
  under the 20-key rule). "Open in a new tab" no longer unlocks signing. Falls back to the browser viewer + 4-second unlock if PDF.js or the
  file can't load — **needs the bucket CORS from storage-cors.json** (same as signed copies). Statement now says "this document"; button "Sign".
- **Employee File → Non-Private Docs → Signed documents** (`pfLoadSigned`): every policySigs record for that person (admins or self) with
  category, version, when, signed-as, read-to-end, and "Signed copy" (`polDownloadSigned`; regenerates the copy if Storage read isn't allowed).
  The sign box and signed view say the copy is filed there.
- Nov 16: **Office Bookings overhaul** (`renderOffices` rewritten; `obCss2`, `obWeekHtml`, `obDayHtml`/`obDayWire`, editor `obEdNew`/`obEdOpen`/`obEdDraw`/
  `obEdSave`/`obEdRelease`, `obRetire`; old obOpen/obSave/obView modal removed). Toolbar: site chips, week nav, **Week | Day** toggle (`OB.view`),
  Just mine (`OB.mine`), Book/Request button, ⚙. **Week board**: offices × days (closed days hatched), bookings as pills, ＋ in each cell. **Day
  timeline**: offices × hours; drag across an empty row to book, drag a booking's edge to change its time (opens the editor to confirm).
  **Side panel editor** for everything: who (approvers), office, Weekly/One time, day(s) (new weekly can pick several → one doc per day),
  starts/ends on, start/end time, note; live clash check. Approvers save directly; editing a weekly booking that already started ends it
  yesterday and continues it as a new booking from today (history kept). Requests strip: Approve / Edit first / Decline. Therapists: edit or
  cancel own requests (delete + recreate); for approved bookings "Send change request" (pending, `replaces`) or "Give this office up…"
  (pending `release:true`); approving either retires the original (`obRetire`; `obDecide` handles release/replaces). No rules change.
- Nov 16: **News attachments** — post editor (`hbmNewsEdit`/`hbmNewsSave`) reuses the event attachment picker (HCAL.att/attKeep/attDrop,
  `hcalAttCommit(newsId)` → Storage refLibrary/{newsId}/att_*); saved as `files` on the kv app_news item; chips on news cards (`newsAttOpen`);
  deleted with the post. Upload needs a Storage-admin account (isBootstrap), same as events.
- **Reference documents**: Documents & sign-offs has "+ Reference document (no signature)" (`polEdit(null,true)`: signature off, category
  defaults to Employee Handbook, sign-by/audience hidden via `.pol-signonly`). Staff see "No signature needed" on the card and in the reader.

## Nov 17 2026 — Office booking blocks (placeholders)
- officeBookings doc with `block:true`, `sid:''`, `name` = the block label (required, ≤60 chars). Created only by approvers (CTM/Supervisor+/Admin) via the toolbar "🔒 Block" button or Who → "🔒 Block — placeholder, no person".
- Blocks hold the office: they clash like normal bookings and count as booked hours in utilization; excluded from Valant "used" accounting and `rcOfficeRecs` per-person stats (byPer key `blk|<label>`).
- Weekly or one-time. Rendered grey hatched (`obCls` → 'k', `obWho` prefixes 🔒). Therapists see it read-only with a "held by the CTM" hint.
- "👤 Assign to someone" converts a block to a normal booking (sets sid/name, `block:false`).

## Nov 17 2026 — Office booking approvers (per site)
- Homebase Settings → Office settings → "Who can approve at <site>": Admins/Super Admins always; checkbox for the site's CTM / CPM (title-detected, `obIsCtmOf`); plus "Also allow these people" (any active staff, any team).
- Stored in Firestore `officeApprovers/{site}` = {ids:[staffId], ctm:bool, updatedBy, updatedAt} via `window.officeApprStore` (all/set); loaded into `OB.appr` by `obLoad`. `obApprCfg(site)` → {ids, ctm}; `obCanManage(site)` uses it. Picked people also see that site (`obSitesVisible`).
- Saved with the rest of the site's Office settings (`obsSave`; draft `OBS.draft.appr`; UI `obsApprHtml`/`obsApprCtm`/`obsApprAdd`/`obsApprDel`).
- firestore.rules: new `isOfficeApprover(site)` lets picked people create/update/delete officeBookings at that site; `officeApprovers` read = signed in, write = Admin. **Rules deploy needed.**
- Note: Supervisor-level accounts still pass the rules at any site (unchanged); the CTM checkbox only controls the app UI.

## Nov 17 2026 — Event RSVP comments + Who's going
- RSVP comment box (optional, ≤500 chars) under the RSVP buttons on calendar event cards; saved with the RSVP click or via "Save comment". Private: stored separately in Firestore `eventRsvpNotes/{eid}__{sid}` = {eid,sid,note,at} (rsvpStore.notesMine/notesFor/setNote/removeNote). Only the author + Admins read.
- "Who's going" on every RSVP event card for everyone who can see it (`hcalWhoHtml`): Going chips (you first, +guests, first 10 then "+N more"), Maybe names. Names only, never comments. `hcalRsvpLoadAll` now runs for everyone from `hcalLoad` (RSVP events ended ≤14 days ago).
- Organizer "See responses" modal has a Comments section; CSV gains a Comment column.
- firestore.rules: `eventRsvps` read opened to all signed-in; new `eventRsvpNotes` match. **Rules deploy needed.**

## Nov 17 2026 — Needs your attention sections, alert statuses/threads, full event view
- My Homebase → Needs your attention now has sections (`.hs-sec` / `.hs-secb`, hidden when empty by `homeWatchAlerts`):
  **Practice alerts** (`home-practicealerts` + individual alerts in clinical/documentation/hr/credentialing/compliance realms → `home-adminalerts`),
  **Billing & Ops alerts** (realms in `SA_OPS` = billing, scheduling, it, other → `home-opsalerts`), **Your to-dos** (`#home-todo`: everything else).
  Only to-dos rotate in the ticker (`homeAlertsClamp`); the header count covers all.
- staffAlerts gain `st` ('seen'|'working'|'question'|'moretime'), `stAt`, `eta`, `thread[{who:'emp'|'iss',name,kind,text,at}]` (≤40), `newFor` ('iss'|'emp'|''), `issuedBySid`.
  Employee row (`saEmpRow`, state `HSA`): status buttons + Mark done; Question / Need more time / Reply open an inline box. Issuer: `homeLoadAlertUpdates` (`#home-alertupd`, alerts they sent with `newFor:'iss'`; legacy alerts match by issuedBy name) → `saThread` modal (reply, Mark resolved). Status pills + "Updates" also in the Employee File alert list (`saList`) and Homebase Settings → Practice alerts.
- firestore.rules: staffAlerts employee update may touch status/ackAt/ackBy/st/stAt/thread/newFor/eta (validated). **Rules deploy needed.**
- Full event view `hcalOpenEvent(eid)` (`#hcal-ev`, state `HEV`): picture, details, PDF attachments rendered inline with PDF.js (first 6 pages, click = open full size; iframe fallback), other attachments, RSVP + comment + Who's going (`#hev-dyn`, refreshed from `hcalPaint`). Opened from the event title / "Open event →" on calendar cards and the RSVP alert. `hcalCmEl` scopes the comment box to the open view.
- PDF.js preview of Storage files needs the bucket CORS (`storage-cors.json`, gsutil) — otherwise it falls back to the browser viewer.

## Nov 17 2026 — Office permissions in Roles & permissions
- New abilities (PERM_CAPS / `PERM_OFFC`): `approve-offices` (approve/decline, book for others, blocks — every site) and `manage-offices` (Homebase Settings → Office settings: offices, names, notes, order, hours/open days, per-site approvers). Any level can be given them.
- Roles/levels saved before this have no `offCaps` flag → keep the old rule (Admin level and up have both). Saving a role/level sets `offCaps:true`; the editor pre-ticks both for legacy Admin/Super Admin records (`permOffcLegacy`).
- `obCanManage` = hbCan('approve-offices') || per-site approvers (officeApprovers/{site}) || site CTM/CPM. Office settings section + the ⚙ on Office Bookings follow hbCan('manage-offices'); `canSeePage('admin')` allows it too.
- Server copy: `officeApprovers/_perm` {approve:[staffId], manage:[staffId]} written by Admins (`obPermSync`, on every Roles & permissions save and when an Admin opens Office settings; `permCanFor(s,cap)` computes effective abilities). firestore.rules `officePermHas('approve'|'manage')` lets those people write officeBookings, officeApprovers/{site} (not _perm) and kv app_office_rooms / app_office_cfg. **Rules deploy needed.**
- The approvers card in Office settings lists everyone with "Approve office bookings" (link to Roles & permissions).

## Nov 17 2026 (later) — Needs your attention simplified; "alerts" → "notifications" in the UI
- The Practice / Billing & Ops / To-dos sections were too busy: Needs your attention is one list again (all notifications + to-dos, critical pinned, rotating, "Show all"). Practice news stays its own card.
- Notification rows are compact (`saEmpRow`): right side **Respond ▾** (opens the status chips: Seen / Working on it / I have a question / Need more time) and **Done ✓**; the current status shows as a small pill; the thread collapses to "💬 N messages" (`saThrToggle`, `HSA.thr`); an unread reply from the sender shows inline with Got it / Reply. Rotation pauses while a response panel (`.sa-pan`) is open. Functionality unchanged.
- Admin-facing wording now says "notification(s)" (Practice notifications, Send a notification, Notifications & flags, Send notifications to employees …). Code names, Firestore collections (staffAlerts, kv app_practice_alerts) and the `issue-alerts` capability key are unchanged.

## Nov 17 2026 — Handbook & Manuals (merged page) + document views
- Employee Handbook and Clinical Policies & How-To Manuals merged into ONE page: My Homebase → **Handbook & Manuals** (page id stays `clin-policies`, nav `#nav-clin-policies`; `showPage('handbook')` and `clin-howtos` redirect to it). Tabs: `hpol` Employee Handbook · `pol` Clinical Policies Manual · `chowto` Clinical How-To Manual ("Coming soon" card + any documents placed there). Only those three tabs (extra tabs for handbook chapters / How-To drafts / old manual removed Nov 17 at Michael’s request — their library content is kept, just not shown). Custom roles that had the old `handbook` page still get the merged page.
- Documents carry `sec` ('hpol'|'pol'|'howto', `POL_SECS`) and `order`; `polPageOf` uses `sec`, else the category mapping. Nav badge = all documents to sign.
- Homebase Settings → Documents & sign-offs: section + category filters; rows grouped by section with ↑/↓ (`polReorder`), Move (`polMove`), signature on/off (`polToggleSign`), Stats, Edit (section, category, signature, sign-by date of the current version), Delete (`polDelete`: hard delete when nobody signed; otherwise `status:'deleted'` — hidden everywhere but kept so signed copies in Employee Files still open). `policyStore.remove` added.
- Views: `policyViews/{pid}__{sid}` {pid,sid,v,first,last,n(increment),readToEnd,endV,endAt,pages,name} written when someone opens a document (`polViewLog`) and when they reach the end (`polViewEnd`). Stats: "👁 viewed X/Y" per row; the document's Stats page has **Who has opened it** (filters, CSV) for everyone in its audience, signed or not; reference-only documents show views + versions. firestore.rules: new `policyViews` match (own write, Admin read). **Rules deploy needed.** Views count from Nov 17 2026.

## Nov 17 2026 — Capacity chart data labels
- Capacity chart (`dataLabels` in the cumulative chart builder): each quarter benchmark is labelled "Q1/Q2/Q3 goal N", the year-end benchmark "Year-end goal N" (bold navy), and each COMPLETED quarter gets "Actual N (x%)" at its last plotted pay period (status colour). Labels go up-left / down-right of their point (both lines rise to the right) and swap sides when actual is above the goal so they don't collide; white halo via paint-order stroke. The in-progress quarter keeps the existing "Through PPn · N hrs" marker.

## Nov 17 2026 — Standard KPIs (note completion + no-shows)
- One set of KPIs everywhere (`kpiRates`, `kpiCardHtml`, `kpiSitesTableHtml`, CSS `kpiCss`): **Note completion** = notes signed after 24 hrs (count + % of signed notes; `late24` = signed > 1 calendar day after the session) and avg days to sign, each vs practice; **No-shows** = no-show rate (paid + unpaid ÷ sessions + no-shows) vs the person's site and vs the practice. Lower is better for all three.
- Where: Capacity Dashboard detail (replaces the old 6-tile "Progress this year"; sessions-by-type table kept), Capacity Dashboard overview bottom (`#cap-kpi`, practice + each site), Pay Period Snapshot (`#ps-kpi`, the person's YTD through the shown period), My Team (top tiles, "team vs practice" rows, per-person columns "after 24 hrs" and "no-show · site"; Late-notes flag = ≥20% signed after 24 hrs (≥40% needs action)), Report Center → **✅ KPIs** tab (practice, sites, each clinician).
- Data: `ppuProgressOf` counts `late24`; `app_practice_stats[ppId]` gains `late24` + `bySite{team:{sessions,noShows,signed,daysSum,late24,unsigned,clinicians}}`; `app_team_stats` gains `late24`. Older closed periods are rebuilt from their frozen snapshots by `kpiBackfill()` (Super Admin; runs automatically once when a Super Admin opens Capacity Dashboard / Report Center → KPIs and data is missing; also a "↻ Rebuild KPI history" button). No rules change.

## Nov 18 2026 — Repeating events
- Event editor: **🔁 Repeats** (Does not repeat · Every day · Every weekday · Every week · Every 2 weeks · Every month (same date) · Every month (same weekday, e.g. 2nd Tuesday) · Every year) + **Ends** (Never · On a date · After N times). Stored as `ev.repeat={f,until,count,skip[]}` in kv/app_events (no new collection, no rules change).
- Occurrences are virtual: `hcalOccDates(e,to)`, `hcalOcc(e,date)` → id `'{seriesId}@{date}'`, `sid`=series, `occ:true`; RSVP-by / reminder dates shift with each date. `hcalExpand(list,from,to)` is used by the calendar (month dots + list), RSVP loading and the RSVP reminder; `hcalFind(id)` resolves an event or occurrence everywhere (event view, RSVP, comments, attachments). Each occurrence has its own RSVPs, comments and Who's going (eventRsvps ids use the occurrence id).
- Calendar "Coming up" shows a repeating event's next date only (pick a day to see others). Cards/event view for an occurrence: **Edit series**, **Skip this date** (`hcalSkipDate` → `repeat.skip`), **Delete series**; skipped dates can be restored in the editor. Homebase Settings → Events lists the series with its repeat text (upcoming until the series ends: `hcalSeriesLast`).

## Nov 18 2026 — Fix: "Edit their own profile" button not showing
- The "✏️ Update my information" button was only rendered at the very bottom of the Employee File (`#m-actions`), so people with the ability never saw it. It now also sits in the profile header (`#m-self-top`, `selfEditButtons(p)`), cleared when other records/applicants open.
- `selfEditAllowed` also accepts the record a Super Admin is "viewing as" (so testing via View-as matches what the employee sees), and the button re-checks once Roles & permissions finish loading (`loadPermRoles().then(...)`) in case the file opens first.
- Reminder: a custom role's own abilities decide for people in it — tick "Edit their own profile" on that role too, not just on the access level.

## Nov 18 2026 — Permissions rebuild (in progress)
- Plan (approved): Stage 1 inventory → Stage 2 real Roles & permissions screen in practice mode (templates + per-person, "What would change" report) → Stage 3 app switch with Super Admin on/off toggle (bootstrap accounts always full) → Stage 4 server rules accept old roles OR new perms, then old removed → Stage 5 cleanup.
- Model (from the approved mockup, `Claude outputs/permissions` + /mnt/user-data/outputs/permissions-mockup.html): areas × {Doesn't see, View only, Manage} × whose data {own, supervisees, site, all}; templates Everyone (auto), Super Admin (Manage on everything, locked), SLT (auto from Senior Leadership; no other SLT pay rates; can't grant Super Admin or 🔒 items), Leadership, CTM/CPM, Clinical Supervisor, HR, Billing, Credentialing, Intake, Front Desk/Ops, Marketing; a person can hold several (widest wins) + per-person tweaks; change log.
- Michael's rule: at go-live everyone except Super Admins starts at the lowest level (Everyone baseline) unless assigned in practice mode.
- Stage 1 inventory: `Claude outputs/permissions/stage1-inventory.md` (268 app checks in 162 functions, all mapped; rules blocks mapped; flags listed).
- Stage 1 decisions (Nov 18): go-live = Super Admins only keep full access; new areas added: Private personal details, CAQH & PECOS logins 🔒, Supply Ordering, Therapy Thrive; "See it as" stays Super Admin-only (not a permission); clearing a pay period's hours lives under Payroll Processing (Manage).
- **Stage 2 built (practice mode):** Homebase Settings → "🧪 Permissions (new)" (section `perm2`, shown to whoever can manage roles). Code: `PV2_CAT` (areas: [key,name,[view text, manage text],levels,scoped,🔒]), `pv2Defaults()` (12 templates; others start from Everyone), `pv2Load/pv2Save` (kv/app_perm_v2 {tpl, ppl:{sid:{tpl:[],ov:{}}}, log}), `pv2TplOf` (Everyone + SLT auto from Senior Leadership role + Super Admin from level + assigned), `pv2Eff` (widest wins; per-person overrides; Super Admin can't be overridden), `pv2Suggest` (templates suggested from title/service types), `pv2Today` (today's access per area, evaluated as the person by temporarily swapping currentViewer/currentRole/VIEW_AS_ID — approximate), `pv2Diff`, UI `pv2Render/pv2Paint` (tabs Templates · People · What would change · Change log), `pv2Set` (🔒 rows need a Super Admin editor; SLT detection via `pv2Editor`). NOTHING reads these settings for access yet — Stage 3 adds the switch.
- Nov 18: the new screen IS "🔐 Roles & permissions" in Homebase Settings (section `perm2`); the old screen moved to "🗂 Current roles (in effect now)" (section `roles`) with a banner pointing to the new one. Profile Admin-actions link and Office settings link go to the new screen.
- Nov 18: Roles & permissions uses the mockup's row layout (area name | three boxes | whose data); on that section Homebase Settings' menu folds into a row across the top (`.hbm-wide`) to give the grid room; template/people lists are chip rows above.

## Nov 18 2026 — Site safety: panic buttons & safety protocols
- My Homebase → Your Site & Emergency has a red "🚨 Panic button & safety protocols" button → popout (`safetyOpen`, `#safety-modal`) with a quick-action banner and two tabs: Panic buttons · Office Safety Policy (Michael's text, lightly formatted). Print button prints both.
- Text in kv/app_safety_doc {panic, policy, updatedAt, updatedBy}; defaults `SAFETY_DEFAULT` in code (people named by ROLE only — names go in via the editor, never in code). Rendered with `libRender` markdown.
- Edit = `safetyCanEdit()` (manage-homebase today). New permission area `safety` ("Site safety: panic buttons & protocols", View only / Manage; Everyone = View; Front Desk/Ops = Manage).
- Nov 18: "Update own demographics" set to Manage on the NEW Roles & permissions screen now works immediately (bridge in `selfEditAllowed` via `pv2Eff(p).selfdemo`; PV2 loads when an Employee File opens). Old ability `edit-own-profile` still works too. Form = SELF_FIELDS only (names, pronouns, DOB, address, alternate phone/email, emergency contact) — no start date, title, team, capacity or pay. TODO Stage 4: tighten firestore `staff/{sid}` self-write to those keys (today rules let a person write any field of their own staff doc; other self-service writes like CEU must be whitelisted first).

## Nov 18 2026 — First Date Working in Office + 90-day ramp
- New profile field `First Office Date` ("First date working in office", clinicians; shown under Date of hire; edit form `#ef-office`, date input). `capRampStartRaw(s)` = First Office Date, else Date of Hire (silently).
- Capacity goal is 0 before the ramp start; ramp = 90 days in 30-day steps from it (`rampFraction`: 1–30 25% · 31–60 50% · 61–90 75% · 91+ 100%). `capHireDate`, `daysSinceHire`, `capRampEnd` (+90), `capRampCheck`, `capUsesRamp` (90), starting-capacity and capacity-dialog "From the start" all use the ramp start. Goal cache key includes First Office Date.
- `ONBOARDING_DAYS` = 90: Onboarding→Active promotion, `isRamping` flags ("New hire — ramping up"), HR tiles count from the ramp start. Hire date still drives anniversaries, tenure, raises etc.
- Existing ramping clinicians' goals change (longer, slower ramp) — expected.

## Nov 18 2026 — Signing: no scroll gate + click-to-sign legal name
- Signing a document no longer requires scrolling to the end of the in-page reader (people may read it in the "Open in a new tab" pop-out). The statement checkbox and name field are enabled immediately; reaching the end in the reader is still recorded on the signature (readToEnd/pages/readEndAt) when it happens.
- Name field offers their legal name (`staffLegalName`) as a datalist suggestion plus a "✍ Sign as <legal name>" button (`polUseName`) that fills it. The existing mismatch confirm still applies if they type a different name.

## Nov 18 2026 — Fresh start at capacity changes
- Any Weekly Capacity change (up or down, always automatic, applies to changes already entered) forgives the shortfall built up before it: at the start of the pay period containing the change, the cumulative goal drops to the hours actually credited by then (if behind); being ahead is kept. Only applies once all pay periods before it have hours entered.
- Code: `capActualPeriods`, `capGoalTables(s)` → {raw, adj, forg}; `capGoalTable`/`capGoalTo` = adjusted (attainment, benchmarks, annual goal, chart pace, catch-up); `capGoalToRaw`/`capGoalBetween` = true day goals (per-pay-period "expected", Report Center windows). `capForgiven(s)` lists forgiven hours; shown in the dashboard's "goal is adjusted" note. Cache key includes the person's entered hours.
- Example: 25→15 hrs/wk on 7/6 with 450 of 570 hrs done → year goal 450 + 342 = 792 (120 hrs forgiven); if ahead (600), goal stays 570 + 342 = 912.
- Nov 18: "First date working in office" renamed **First Client Day** everywhere it shows (data key stays `First Office Date` — no migration). New profile field **Orientation date** (`Orientation Date`, everyone, date input `#ef-orient`) — stored only, not used in any calculation yet.
- Nov 18: Roles & permissions no longer autosaves — edits are staged (`pv2Stage`, PV2.pending/dirty) and saved with Save bars at the top (sticky) and bottom (`pv2SaveBar`, `pv2Commit`, `pv2Discard`); leaving the section with unsaved changes asks first.
- Nov 18 (later): "Update own demographics" now defaults to **Manage** on the Everyone template (one-time upgrade of saved settings unless the Everyone row was deliberately changed; flag `selfdemoV2`). Everyone sees "✏️ Update my information" on their own file; set View only on a template or person to block it. Admins (edit-profiles) still use the full editor.

## Nov 18 2026 — Permissions Stage 3 + 4: the app AND firestore.rules follow the new Roles & permissions ⚠ rules
- **Switch:** `kv/app_perm_v2.on` (missing = ON) + server copy `permConfig/live.on`. Roles & permissions shows a banner with
  "↩ Switch back to old roles" / "Turn new permissions on" (Super Admins, `pvSetOn`). Off = the old access levels + custom roles,
  in the app and the rules, instantly. The app runs on the SAVED copy (`PV2.live`, `pvSetLive`), never on unsaved edits.
- **App (Stage 3):** core helpers next to `currentRole()`: `pvOn`, `pvIsSA` (Super Admin level / bootstrap / previewing the SA template),
  `pvMe` (effective map, cached), `pvLv`, `pvSc`, `pvCan(area,lv)`, `pvSees(area,lv,sid)` (whose data: own / supervisees / site = Team / all; View uses the widest scope of any template that shows the area (`vsc` from `pv2EffIds`), Manage the scope that came with Manage),
  `pvIds`, `pvWide`, `pvSolo`. Drop-ins used at every former admin check: `pvA(area,lv,sid)` (was isAdminView), `pvS(area,lv,sid)`
  (was isSuperAdminView), `pvAllA` (needs whose data = all) — each returns exactly the old check when the switch is off.
  With it on: `isAdminView()`/`isSuperAdminView()` = Super Admin only (there is no Admin), `currentRole()` = 'superadmin' | 'therapist',
  `hbCan(cap)` maps to areas (`PV_CAPMAP`; profile abilities check the open Employee File, `PV_TGT` via `pvSetTgt` in openRoster/closeDetail;
  SLT never sees other SLT members' comp), `canSeePage` → `pvPage` (`PV_PAGE` page→area), `visibleStaffIds(area)`, `clScope` (team area),
  `hbmSections` → `pvHbmSections` (one area per settings section), office/calendar/safety/library/intake helpers.
  `pv2Today` evaluates the OLD rules (`PV_FORCE_LEGACY`). `pv2Eff(s,D)` / `pv2EffIds(ids,P,D)` / `pv2TplOf(s,D)` take the data set.
- **Identity:** boot loads `pv2Load()` before `__applyIdentity`. With the switch on only real Super Admins (`window.PV_REAL_SA`: level
  superadmin or bootstrap) get ADMIN_SESSION / god view; everyone else sees Homebase as themselves. `saveStaffArray` lets non-SA
  writes through for records in their Roster / Private details / CAQH Manage scope (`pvStaffWriteOK`); `syncUserRoles` lets
  Roster = Manage create a NEW hire's userRoles entry at Therapist level only.
- **See it as:** top-bar menu lists every template (`setViewAs('tpl:<id>')` → `PV_PREVIEW`, shown on your own record). The preview
  build's "See it as" lists Super Admin + each template (CTM on "Sample CTM", Clinical Supervisor on "Sample Supervisor", others on
  "Sample Therapist") + old roles (only meaningful when switched off).
- **Server (Stage 4):** the app writes `userPerms/{email}` = {sid, lv:{area:1|2}, vsc/msc:{area:'sup'|'site'|'all'} (whose data for viewing /
  managing; missing = own), vids/mids:{area:[staffId]} (supervisees / same-Team list), team} for every staff member (`pvDocFor`, `pvPublish`, `window.permStore`) on every Save, and a Super Admin's
  sign-in republishes when anything changed (signature `pvHash`; teams/supervisors/hires). firestore.rules: `permsOn()`, `pvLv(a)`, `pvSc(a,n)`,
  `pvAll(a,n)`, `pvFor(a,n,sid)`, `pvSite(a,site)`; while on, `isAdmin()` = Super Admin and old Supervisor grants (`isOldSupervisor`,
  `officePermHas`) stop. Every block now also accepts the matching area (see the comments in firestore.rules; kv keys via `kvArea`).
  `userPerms` write = Super Admin, or Roles & permissions = Manage for others (not yourself); `permConfig` write = Super Admin.
- **Self-write tightened (always):** your own `staff` doc may only change Legal/Preferred Name, Pronouns, Clinician (display name),
  `_ceus`, `_files`, and Employee Status → 'Active' (the auto promotion); names need "Update own demographics" = Manage when on.
  Own `staffPrivate` write needs that too when on.
- **Known limits:** Storage rules still use the hardcoded bootstrap accounts (no Firestore lookups in this project's Storage rules), so
  uploads to library/event/private-doc storage paths stay with those accounts. Blob keys (kv app_comp_data, app_comp_checklist) can't be
  split per person — they need whose data = All. Collection-wide reads (e.g. everyone's private details, all notifications) need whose
  data = All; site/supervisee scopes work per document. 🔒 rows are protected in the app; the rules trust whoever can save Roles &
  permissions. A few screens have no read-only mode yet, so their View = Doesn't see (Payroll Processing page, Insurance Catalogue,
  Benefits, Payroll Settings need Manage). Firestore emulator wasn't reachable from the build machine, so the rules were reviewed by hand.
- **Deploy:** `firebase deploy --only hosting,firestore:rules --project advance-intranet`. Right after: a Super Admin signs in (publishes
  everyone's permissions + switches the server on), then assigns templates in Roles & permissions → People and Saves.

## Nov 18 2026 — Leave of absence tied to Status
- The leave dates (`staff._leaves`) drive "On Leave": `effectiveStatus` shows On Leave while a leave covers today and goes back to
  Active/Onboarding once every leave has ended (`staffLeaveNow`, `staffLeavesAllEnded`); saving leave dates also sets the stored
  Employee Status (`staffLeaveSyncStatus`). The roster status pill now uses `effectiveStatus`.
- Employee File edit form: choosing (or keeping) Status = On Leave always shows the leave date fields — a new leave, or the
  current one to change (`staffLeaveCurrentIdx`); a leave can't be saved without a first day.
- One leave editor: **⏸ Leave of absence…** (`leaveDlgOpen` / `leaveDlgSave`) — Admin actions, the edit form link, and Capacity
  adjustments (+ Leave / Set return) all open it (date inputs, several leaves, overlap check). Old prompt versions kept as *Old.
- Capacity Dashboard → Capacity Attainment by Week: pay periods with leave days show ⏸ ON LEAVE (· N days when partial); a fully-on-
  leave period shows 0 expected and an ON LEAVE pill instead of OVER/UNDER, and appears even when payroll recorded no hours (`capPeriodRows` leaveDays).

## Nov 18 2026 — Renames
- **Report Center → Insights & Reports** and **Homebase Settings → Homebase Control Panel** everywhere they show (nav, page titles,
  tour, links, help text). Page ids (`report-center`, `admin`) and code names (`rc*`, `hbm*`) are unchanged. Older notes in this file
  still use the old names.
- Nov 20: Handbook & Manuals fix — switching tabs while a document was open kept showing that document (POL.open survived the tab
  change). `libSwitch` now clears `POL.open`/`POL.adm`, and `polRender` drops an open document that doesn't belong to the current tab.

## Nov 22 2026 — Capacity Dashboards fill from uploaded (not yet closed) pay periods
- Before: clinical hours reached the Capacity Dashboard only when a pay period was CLOSED (`ppuWriteCapacity` at close).
- Now: every open pay period of the capacity year that has a Valant upload is computed exactly like Payroll Processing and its hours
  are written as PROVISIONAL (`capProvWrite`, `capSyncOpenPeriods`; marker `CLINICAL_HOURS_DATA.prov[idx]`). It runs 1.5 s after
  Payroll Processing computes an open period (upload, links, corrections, approvals), once per sign-in for people who can manage
  Payroll Processing, and from Capacity Dashboard → 🗓 Pay periods → "↻ Update from uploaded pay periods". Closing replaces them
  (prov cleared). Pay-period rows show "NOT CLOSED YET".
- Safety: `capLoadPersistedHours` / `capLoadPersistedGroupHours` no longer write the empty built-in copy to Firestore when a read
  fails (that could erase everyone's hours), and `ppuWriteCapacity` re-reads the saved hours before writing.
- flows.js: the office-booking flow now books in next week (this week's cell could be in the past).

## Nov 22 2026 — Capacity changes: tier change, notes, part-time → full-time ramp
- Change capacity dialog (`capDlgBody`) has **Capacity tier** (current tier + "New tier" select; a different tier = tier change,
  also sets the profile's Capacity Tier) and a **Note** (≤400 chars). Saved on that `_capHist` entry: `tier`, `tierOld`, `note`,
  `ramp`, `by`, `at` (`capDlgSave`). Lists show them (`capHistExtra`); the dashboard's "goal is adjusted" banner (`capAdjustNotes`)
  lists each change with its tier change, ramp and note — seen by the clinician, their leaders and admins.
- **Part-time → full-time ramp:** Part Time/Fractional → Full Time/Salary with more hours (`capTierRamps`) gets a 60-day ramp from the
  start date (`CAP_TIER_RAMP_DAYS`): days 1–30 = old + ½ of the increase, 31–60 = old + ¾, full from day 61 (`capWeeklyAt`, entry
  `ramp:{old,days}`). The dialog shows the steps and the goal effect includes them (`capEfEffect(..., newTier)`). Other increases take
  effect immediately. Not applied to "From the start" (starting capacity — the new-hire ramp covers that).
- Nov 22: Leave in the dashboard notes — each leave now reads like "Leave of absence 8/24 – 10/4 (6 weeks): no clinical hours are expected on
  leave days, so the goal line stays flat during the leave and this year's goal is N hrs lower than it would have been. Note: “…”"
  (`capLeaveNoteText`; N = the day goals the leave removed within the capacity year). Leaves can carry an optional note (≤200 chars,
  `_leaves[].note`) from the Leave of absence window or the edit form (`#ef-leavenote`); the UI asks to keep it general (no medical details).
- Nov 22: My Homebase → Your Site & Emergency is smaller: emergency numbers fold into one line (label · 911 · Show ▸; open/closed
  remembered in localStorage `hb_em_open`; `homeEmergencyCollapsed` wraps `homeEmergencyInner`, site picker still inside). The panic
  button stays visible. **My office** (this week's bookings, Book an office, Calendar) moved into this card (`homeOfficeSecHtml`, same
  `#home-ob` loader); the separate My office card beside the capacity card is gone (`homeCapRowHtml`).
- Nov 22 (later): **🚨 Emergency & Safety page** (page `safety`, nav under My Homebase, open to everyone; `safetyPageRender`/`safetyPaint`):
  red 911 + panic-button banner, emergency numbers card with site picker (`safetyNumbersHtml`, `SAFETY.site`: 911, site police/fire,
  crisis lines, leadership on call, address), and tabs Panic buttons · Office Safety Policy (editable with Site safety = Manage) · Crisis
  guide (the old Crisis & Safety page's Clinical Response Guide, `#crisis-proto`, `safetyCrisisHtml`). `showPage('crisis')` redirects
  here; `safetyOpen(tab)` now opens this page (the popout is retired). Your Site & Emergency widget shows one line instead
  (`homeEmergencyLine`: 🚨 Emergency · 911 · "Emergency & safety page →"); `homeEmergencyCollapsed` is unused.
- Nov 22: Locations (Homebase Control Panel) buttons renamed for clarity — **+ Add location**, **Change**, **Deactivate…** / **Reactivate**
  (same `locEdit` / `locClose` / `locReopen`). Open locations with no offices (e.g. RSTI) get **＋ Add offices** (`locEdit(code,true)`
  focuses "Offices for booking"); saving creates Office 1..N in kv app_office_rooms, which gives the site its Office Bookings calendar.

## Nov 22 2026 — Group control panel + Meeting & admin time settings ⚠ rules
- Homebase Control Panel → new side-menu group **Groups & meetings** (Meeting & Admin Time = Manage under new permissions; Admins in
  the old roles):
  - **👪 Group control panel** (`hbmRenderGroups`, list + edit modal `grpEdit`/`grpSave`/`grpDelete`): kv `app_groups` {items:[{id,name,
    code (Service Code Workbook group code), status active|paused|ended, site, format, dow (0=Mon), start, startDate, endDate, leaders:[sid],
    notes}]}. Filters Active/Paused/Ended/All + site. "Current" = active and today inside its dates (`grpIsCurrent`, `grpCurrent`).
  - **🕒 Meeting & admin time settings** (`hbmRenderMtgSet`, `recmEdit`/`recmSave`/`recmDelete`): kv `app_mtg_recurring` {items:[{id,name,
    type (a CONFIG.meetingTypes label → pay rate), sched (text), start, mins, teams:[] (empty = everyone), status active|inactive}]}.
- Meeting & Admin Time page now has two tabs (`MTG_TAB`, `mtgTabsHtml`): **👪 Log a group I led** (group-session type only, auto-selected;
  "Group" is a dropdown of ALL current groups + "Other (not listed)" — `mtgGroupSelHtml`/`mtgGroupPicked` fill the service code and usual
  start time) and **🕒 Meetings & admin time** (all other types). Group prep & admin also picks from current groups. Choosing a kind of time
  that has recurring meetings shows "Which meeting?" (`mtgRecmPaint`/`mtgRecmPicked`: fills start + length). The chosen group / meeting
  name is saved in the entry's existing `group` field (no new key — meetings rule caps fields at 20). Editing an entry opens the right tab.
- firestore.rules: `kvArea` maps app_groups / app_mtg_recurring → 'mtg' (Manage writes). **Rules deploy needed.**
- flows.js: group-session flow uses the new tab + "Other".
- Nov 22 (later): "Log a group I led" simplified — service code is only **In person · 90853 (G 90853)** or **Virtual · 90853 (GV 90853)**
  (two buttons, `mtgSetGCode`, hidden `#mtg-gcode`), plus Attended, plus **Date only** (no start/length; the entry stores the group's usual
  start time from the Group control panel if it has one, else none; always 60 min). Group control panel: no code picker — "In person or
  virtual" sets the code (`grpCodeOf`); blank = the leader picks each time. `mtgClock('')` returns ''.
- Nov 22 (later): Meeting & Admin Time form redesigned (Michael picked "form + summary card", both tabs): fields in a two-column grid on
  the left (`mtgFormCss`, `.mf-*`), a sticky "You're logging" card on the right with the live summary (`mtgDurPreview` → `mtgSumCard`
  rows; missing items in amber) and the Submit buttons. Groups: Group · Date · Clients who attended (−/+ stepper, `mtgHcStep`) · In person /
  Virtual segmented (90853) · note. Meetings: "Kind of time" is a dropdown (`#mtg-type`, `mtgPickTypeSel`; `mtgCurType` reads it first) with
  its description under it · Which meeting? · Which group? (prep) · Date · Start time · How long chips · note. Today/Yesterday chips removed.

## Nov 22 2026 — Capacity Dashboard detail redesign (Michael picked option 1 of capacity-options-4) ⚠ rules
- `capDrillHTML` layout (`.cdx-*`, `capCdxCss`): top row = attainment ring + text | the "hours to add" catch-up callout; full-width chart
  card with a **View** dropdown (`capViewSet`, `CAPV.view`): Year to date (the existing cumulative chart with its quarter/year-end/actual
  data labels) · Over/under by pay period (diverging bars from `capPeriodRows`, value labels, leave bars, click → `prOpenSheetForPP`) ·
  No-shows (stacked charged 11111 / not charged 11112 per pay period, bar height = rate, dashed practice average) · Groups (90853 count)
  · Session types (individual / couples-family / groups). Then a quarters row (goal vs actual; current quarter = quarter to date), then
  tabs (`capTabSet`): Sessions & clients (pie + sessions-by-heading + the old hours breakdown) · No-shows & notes (explicit sentences vs
  site and practice averages, charged vs not charged) · How your goal is figured (`capAdjustBannerHtml` + admin Capacity adjustments,
  moved out of the detail header) · Pay period table. Graph notes at the bottom.
- Session kind (`capLineKind`): group = 90853 / "G "/"GV " codes / logged groups / group headings; couples = 90846, 90847, COUPFAM codes or
  Couples/Family headings; everything else individual. No-shows and supervision are left out of session counts.
- Data: `capVLoad(sid)` reads the person's latest ppu payStatements per pay period (so the extra views and tabs show for the clinician,
  leaders with Pay Period Snapshot access to that person, and Super Admins; others see a short explanation) + kv app_practice_stats
  (practice + bySite[Team]). Cache `CAPV.data[sid]`.
- **Graph notes:** Firestore `capNotes/{id}` {sid, by, byName, date, text ≤400, vis 'all'|'lead', at} via `window.capNoteStore`
  (`capNotesLoad`, `capNoteAdd`, `capNoteDel`). Writers: the clinician (always 'all'), their leaders (Capacity Dashboard view of that
  person) and admins, who choose "Everyone who sees this dashboard" or "Leaders & admins only". Delete: author or admin. No edits.
  firestore.rules: new `capNotes` match + `capLead(sid)`. **Rules deploy needed.**
- Nov 22 (later): Sessions & clients pie restored to the approved mockup — five slices (`capLineKind5`, `CAP_K5`): Individual 60 min
  (90837) · Individual 45 min (90834) · Family / couples · Groups (90853, with session count) · Intake & other; right side = sessions this
  year, individual/family credit hrs and group credit hrs (sum of statement `clin`, stored in hundredths). The chart's View dropdown has a
  pulsing orange "NEW ⟶" tag + orange border until `CAP_VIEW_NEW_UNTIL` ('2026-12-22'; `capViewNewOn`) — it disappears on its own.
- Nov 22 (later): Clicking a pay period on the Capacity Dashboard (cumulative chart dot, over/under bar, or a row of the pay period table)
  no longer opens Payroll Processing / the pay sheet. It shows a small popover next to the click (`capPPAsk`, `#cap-ppask`; Esc / click
  outside / "Not now" closes; positions divide by the body zoom) asking to go to the **Pay Period Snapshot**; "View snapshot →"
  (`capPPGo`) opens that person's snapshot on that pay period (`paySnapGo(sid,start,end)`) with `PSNAP.fromCap` set → a teal
  "← Back to the Capacity Dashboard" bar at the top of the snapshot; back (`paySnapToCapacity`) restores the chart view (`CAPV.view`).
  The snapshot's dashboard button now reads "← My/Their Capacity Dashboard". `showPage` clears `PSNAP.fromCap` when leaving the snapshot.
  `prOpenSheetForPP` is no longer called from the dashboard (kept).
- Nov 22 (later): "Hours by service type" card removed from the Capacity Dashboard detail (Sessions & clients tab = pie + sessions-by-
  heading only; the `breakdown` const in capDrillHTML is now unused). Details tabs are highlighted: "Details · Pick a tab to see more"
  header + a light-navy tab bar of four equal buttons, active = navy (`.cdx-dhead`, `.cdx-tabs`, `.cdx-tab`; 2×2 under 760px).
- Nov 22 (later): **Year-to-date chart restyled to the approved mockup** (same builder in `capDrillHTML`, same hover/click): 1000×400,
  legend on top (actual · goal pace · quarter goal vs actual · 📌 note), month names + light vertical month lines (no y-axis, no quarter
  bands, no PP numbers), green/status-colour actual line (4px, per-period dots hidden until hovered), dashed goal pace, navy dots on
  finished quarters' goals with "Q1 goal N" and a status dot "Actual N (x%)" (higher label up-left, lower down-right), "Year-end goal N",
  "Now N · goal G" at the last closed pay period, shaded "on leave" bands from `_leaves`, and 📌 pins at graph-note dates
  (`capPinsPaint`, layer `.cdx-pins`, svg data-padl/plotw/piny). maxY = max(annual, ytd) × 1.12.
- Details tabs are now five: Sessions & clients · No-shows · Notes (note completion: signed after 24 hrs and avg days to sign vs practice,
  `#cdx-nc`, filled by `capNsPane`) · How your goal is figured · Pay period table.
- Nov 22 (later): Graph notes from the chart — "📌 Add a note to this graph" button in the chart's legend row and "📌 Add a note for this
  pay period" in the pay-period popover (`capNoteJump(iso)` scrolls to the notes form, pre-fills the date, focuses the text; people who
  can't write notes get a toast). Chart colour now follows the attainment score (same as the ring). Year-end label moves clear of the
  Now dot. Preview build: Sample Therapist has a sample leave (PP 18–20, no hours) and three sample graph notes.
- Nov 22 (later): Clicking a 📌 pin on the year-to-date chart opens the note in a popover next to the pin (`capPinOpen`, reuses
  `#cap-ppask` and its close handlers; date, text, author, who sees it; "Remove note" for the author / Super Admins). Pins are keyed in
  `CAPV.pins` by `capPinsPaint`; their click stops propagation so it doesn't open the pay-period popover.
- Nov 22 (later): **No-shows and Notes tabs redesigned** (Michael: the sentence + tile layout was hard to read). Each tab = two cards
  (`.cdx-kg`/`.cdx-kc`): No-shows → "No-show rate" (verdict chip `capVerdict` — Better than / About / Higher than average, lower is
  better; big number + "N no-shows out of M appointments"; comparison bars You / site / practice via `capKBars`) and "When a client
  no-shows" (one split bar charged 11111 teal / not charged 11112 orange with a practice-% marker, then two labelled rows: paid 1 FFS hour /
  not paid). Notes → "Notes signed more than 24 hours after the session" and "Average time to sign a note", same card pattern.
- Nov 22 (later): No-shows charged card now reads as the person's own data: "When your clients no-show" with a chip (About the same as the
  practice / You charge more / less often), two labelled split bars — **You** (bold, with %) and **Practice** (lighter) — via
  `capSplitRow`, and rows "N of your M no-shows were charged / not charged". First card titled "Your no-show rate".
- Nov 22 (later): No-shows tab gets a full-width card **"Your clinical hours: in person vs virtual"** (`capDelCard`): one split bar +
  hours and % in person / virtual / not marked. Each statement line's clinical credit is tallied by delivery (`capLineDel`): the Service
  Code Workbook's `delivery` (now included in the staff-readable kv app_code_guide by `ppuPublishGuide`; `PPU_SEED` as fallback,
  `capDelGuide` caches the map), else the code/description (GV… / "virtual" = virtual, G… / "in person" = in person), else "not marked".
  Re-saving Payroll Settings republishes the guide with delivery.
- Nov 22 (later): the in person vs virtual card moved to the **Sessions & clients** tab (under the pie card; `capSessPane` appends
  `capDelCard(t)`); the No-shows tab is back to its two cards.

## Nov 23 2026 — First Client Day in the Change capacity window
- Confirmed: the capacity goal starts on the **First Client Day** (`First Office Date`) and the 90-day new-hire ramp counts from it
  (`capRampStartRaw` → `capHireDate` → `capTimeline.hire` → `capDayGoal` = 0 before it); the Date of Hire is used only when First
  Client Day is blank.
- Change capacity dialog (`capDlgBody`) has a **First Client Day** date field (+ "Clear (use hire date)"). `capDlgFcd` re-renders the
  dialog with it applied (`CAPDLG.fcd`, `capDlgView`), keeping typed values; the effect box shows the new ramp window and goal to date /
  year goal before → after. It can be saved on its own (no capacity change needed) or together with a capacity change (`capDlgSave`).
  Blocked if an existing capacity change would land inside the new ramp (`capFcdConflict`). An open Employee File edit form is updated
  (`capEfSyncAfterDlg` sets `ef-office`). Header line now reads "hired … · first client day … · new-hire ramp …".

## Nov 23 2026 — Clinical Hours & Attainment Tracking + practice clinical-hours goal ⚠ rules
- Insights & Reports tab renamed **🎯 Clinical Hours & Attainment Tracking** (tab key still `hours`). Its first card is
  **Clinical hours by pay period** (`hrgChartHtml`, practice-wide; hidden when a site is focused): one bar per pay period = the
  practice's credited clinical hours (sum of `capActualPeriods` over all staff — same numbers as the Capacity Dashboards; open
  uploaded periods drawn dashed "not closed yet"), dashed orange goal line, green = met. Click a bar (`HRG.sel`) → that pay period's
  total vs goal and a table by session category (actual from kv app_practice_stats[ppId].byHead clin, closed periods only; heading →
  category `hrgHeadCat`: group → Groups, couples/family → Couples/family, intake/CANS/collateral/screening → Intake & other, else
  Individual) vs each category goal.
- Goal: kv **app_clinical_goal** = {years:{YYYY:{cats:{ind,cpl,grp,oth}, at, by}}}; pay-period goal = sum of categories (default
  1,500 / 200 / 150 / 150 = 2,000; `HRG_DEFAULT`). Edited in Homebase Control Panel → Insights & goals → **🎯 Clinical hours goal**
  (`hrgRender`, `hrgSave`; Insights & Reports = Manage, or Admins in the old roles). firestore.rules kvArea maps app_clinical_goal → 'rc'.
