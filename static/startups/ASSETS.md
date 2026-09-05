# Startup timeline asset provenance

Captured September 5, 2026.

- Design reference: https://chrono.news/
- `chrono-mark.png`: https://media.base44.com/images/public/69a7ace57489e18006d5a137/7545b1e2c_chronoiconlogo.png
- `timeline.jpg`: https://media.base44.com/images/public/69a7ace57489e18006d5a137/d239d6973_wacBSL8GPJt8iGoX5cKTuc.jpg
- `icons/`: SVG control geometry extracted from the rendered Chrono page. Moon,
  sun, search and chevron are its Lucide icons. Topics/layout controls and the
  static account glyph come from its rendered SVGs. Stroke colors are normalized
  for local dark/light theme styling. The account animation is a static frame.
- Typography: Inter, system-ui, sans-serif is Chrono's declared family. Its asset
  inventory contained no font files, so the local page uses the observed system
  fallback instead of adding an unobserved font download.
- `images/`: company artwork and logos from public Startups Gallery company
  profiles, using the source's first landscape hero image. Each record in
  `data/startups/latest.json` records `image_url`, `logo_url`, source article,
  company URL and local paths. Images are cached at their original dimensions.

These are attributed third-party assets, not original Signal artwork. No claim
of ownership or an open-source asset license is made. The new code does not
include Chrono application bundles, API clients, analytics, authentication or
session recording code.
