# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Static marketing website for **THT Orchid Farm** — a family-owned phalaenopsis orchid farm in Đơn Dương, Lâm Đồng, Vietnam. Zero dependencies, zero build steps.

## Running Locally

The pages fetch `varieties.json` via `fetch()`, so they must be served over HTTP — opening `index.html` directly as a `file://` URL will not work.

**With the admin server** (required for variety management):

```bash
pip install flask anthropic
ANTHROPIC_API_KEY=sk-... python3 server.py
# Site:   http://localhost:8000/
# Admin:  http://localhost:8000/admin.html
```

**Without admin features** (static files only):

```bash
python3 -m http.server 8000
```

## File Structure

| File | Purpose |
|---|---|
| [index.html](index.html) | Main landing page (Hero → Varieties → About → Care Guide → Contact) |
| [varieties.html](varieties.html) | Full catalog page — all variety cards |
| [variety.html](variety.html) | Individual variety detail page (driven by `?id=` query param) |
| [styles.css](styles.css) | All styling — CSS custom properties, responsive breakpoints at 900px and 560px |
| [main.js](main.js) | Nav/menu/form/animation behavior |
| [i18n.js](i18n.js) | Internationalization module — loads `translations.json`, swaps `data-i18n` attributes |
| [translations.json](translations.json) | EN and VI string maps |
| [varieties.json](varieties.json) | All variety data — fetched at runtime by every page |
| [server.py](server.py) | Local dev + admin Flask server — serves static files, exposes `/api/*` endpoints for variety management, calls Claude API for AI-generated descriptions |
| [admin.html](admin.html) | Browser UI for adding/publishing/removing varieties (requires `server.py`) |

**Images**: `images/Queen.jpg` (hero), `images/Farm.jpg` (about section), plus one JPG per variety (e.g. `images/THT001.jpg`).

**External dependencies**: Google Fonts CDN (Cormorant Garamond + DM Sans) and a Google Maps embed in the contact section.

## Architecture

**HTML**: Three-page site with smooth-scroll navigation on the landing page. `varieties.html` and `variety.html` are separate documents driven by `varieties.json`.

**CSS**: Single `styles.css` file using CSS custom properties for the color/typography design system.

**JavaScript**: [main.js](main.js) handles:
1. Nav background transition on scroll (transparent → opaque at 60px)
2. Mobile hamburger menu (full-screen overlay, closes on link click or Escape)
3. Scroll-triggered `.fade-up` animations via `IntersectionObserver`
4. Contact form submission (client-side only — shows success state, no backend)

**i18n**: [i18n.js](i18n.js) loads [translations.json](translations.json) and replaces the text content of any element with a `data-i18n` attribute. The language toggle UI exists in the codebase but is currently **disabled** (hidden via `display: none` in styles.css) — do not remove the i18n wiring.

## Adding a New Variety

**Via the admin UI** (preferred): run `server.py`, open `http://localhost:8000/admin.html`, upload a photo and fill in the code — Claude generates name/description copy, you review and publish. Publishing commits directly to `master` and triggers a Netlify deploy.

**Manually**: add an entry to [varieties.json](varieties.json) and the matching keys to both `"en"` and `"vi"` blocks in [translations.json](translations.json). Set `"image"` to `"images/MyOrchid.jpg"` or `null` to fall back to the CSS gradient defined by `"fill"`. Add the image to the `images/` directory. No HTML changes needed — every page fetches `varieties.json` at runtime.

## Deployment

The site is hosted on **Netlify**, deploying from the **`master`** branch. Active development happens on `develop`; merge to `master` to trigger a production deploy.

**Important**: The hero description fallback text lives in two places — the `data-i18n` attribute default in [index.html](index.html) AND the `hero.desc` key in [translations.json](translations.json). Always update both to keep them in sync, otherwise the JS i18n swap will override the HTML fix at runtime.
