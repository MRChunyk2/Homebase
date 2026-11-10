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
