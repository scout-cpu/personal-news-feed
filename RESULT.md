# Startup timeline implementation — September 5, 2026

Added a separate `startups.html` page based on Chrono's captured homepage,
including responsive horizontal/vertical timelines, original control assets,
light/dark appearance, search, funding-stage filters, local saved rounds and
funding details with links to original announcements.

The initial snapshot contains 50 Startups Gallery funding rounds. Assets are
cached locally. The existing Python builder renders the new page and preserves
the daily briefing/archive. The daily workflow now refreshes startup data before
building. UTF-8 handling was verified against the live source; refresh failures
preserve the previous snapshot.

Validation: 28 Python tests passed, JavaScript syntax check passed, desktop and
mobile browser interaction/visual QA passed with no console errors. Screenshots
and comparison notes are in `docs/startup-timeline/` and `design-qa.md`.

No commit, push or deployment was performed. To publish, review and commit these
changes, then push to main using the existing GitHub Pages workflow.
