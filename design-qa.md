# Startup timeline design QA

final result: passed

## Evidence

- Source: https://chrono.news/, captured September 5, 2026 in the Codex in-app browser.
- Source visual truth: `docs/startup-timeline/chrono-desktop.png` and `docs/startup-timeline/chrono-mobile.png`.
- Implementation screenshots: `docs/startup-timeline/startups-desktop.png` and `docs/startup-timeline/startups-mobile.png`.
- Preview inspected: `http://127.0.0.1:8899/startups.html` (staging); final code is the same page in the canonical project.
- Desktop CSS viewport and both image dimensions: 1440 × 1000. Mobile: 390 × 844. Captures are 1 pixel per CSS pixel; no density normalization needed.
- State: dark homepage, desktop horizontal/mobile vertical. The live source is horizontally scrolled to different stories; compare card size, spacing and axis alignment rather than headline identity or its current scroll offset.
- Each source and implementation screenshot was emitted together in one comparison input, including the final post-fix desktop and mobile pairs.
- Full-size card text, metadata, logo and controls were readable in these captures. Separate cropped images were unnecessary; DOM/computed styles additionally grounded typography, dimensions and positioning.

## Required fidelity surfaces

- Typography: matches the source declaration `Inter, system-ui, sans-serif` and its actual fallback (no font files loaded on the source). Desktop headlines 14px/19.25px, normal weight, 0.01em tracking. Mobile 13px/18px. Uppercase dates use 11–12px lettering and spaced labels.
- Layout: desktop cards 280px wide with a 360px pitch, axis at 50vh and 48px stems; 16:9 artwork, 16px card corners, 12px content padding. Mobile spine x=195px, cards x=8px/218px, width=164px. Bottom controls remain fully inside the viewport. Desktop vertical layout and light theme were also inspected.
- Color: black/white themes, #111113 cards, muted zinc text, faint rules, translucent floating controls and source-style theme switch. Metadata is slightly brighter for legibility. The source's animated search border is represented as a static subtle glow.
- Assets: copied source control SVG geometry, logo mark and black-hole art; cached real company profile artwork replaces unrelated news photography. All 50 cards have local artwork. No fabricated illustrations or hotlinked media. Account vector retains its captured static frame.
- Content: Signal branding, actual funding facts and original source links. Source waitlist promotion becomes a provenance/explanation card. Funding stages replace global-news categories. The account control becomes local saved rounds. The detail dialog presents funding facts rather than unprovided article text. These are deliberate adaptations to the requested startup feed.

## Comparison history

1. Initial desktop/mobile match: found an undersized account glyph. Increased its SVG box from 32px to the captured 48px dimensions. Post-fix evidence is in the final screenshots.
2. Reload/focus QA exposed a 17px shell scroll offset that moved the mobile timeline upward. Pinned the main timeline to the viewport and contained scrolling inside it. Final DOM check: main top=0, width=390, height=844, no horizontal document overflow. Final paired screenshots confirm the first node is aligned at y=133 again.
3. Final desktop comparison: axis y=500; card geometry and floating controls match. Final mobile comparison: expected headline-wrap variation from startup content; no remaining P0/P1/P2 findings.

## Interaction and implementation checks

- Search by company returned the expected single record.
- Funding stage Seed returned 15 records, all tagged Seed.
- No-results message and reset restored all 50 records.
- Detail links match the original announcement and company profile.
- Save/remove updates its accessible pressed state; saved rounds persisted across reload. Test saved state was removed afterward.
- Filters, about/source dialog and close controls worked on mobile.
- Both timeline modes and light/dark toggles worked.
- Keyboard horizontal navigation changed the scroll position; Home returned to the beginning.
- No browser warning/error logs in final checks. Visible image load checks passed.
- Python suite: 28 tests passed. Includes funding parsing, responsive-row deduplication, failed-refresh snapshot preservation, UTF-8 response decoding and clean-build integration with HTML escaping.
- `node --check static/startups/timeline.js` passed.
- A live raw-HTML refresh cached all 50 records successfully. No browser/Firecrawl dependency is required in GitHub Actions.

## Follow-up polish / limits

- P3: Chrono's animated header shine, account animation and animated search border are static treatments here.
- Source photography and text intentionally differ. This is a homepage/layout adaptation, not a reproduction of Chrono's account, AI assistant, subscriptions or backend.
- Data includes the first public batch of 50 funding records; no “Load More” pagination. Refresh occurs during the existing daily build, with a dated fallback snapshot on failure.
- GitHub Actions and public deployment were not executed. Changes remain local for review.
