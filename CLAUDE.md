# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Static marketing website for **THT Orchid Farm** — a family-owned phalaenopsis orchid farm in Đơn Dương, Lâm Đồng, Vietnam. Zero dependencies, zero build steps.

## Running Locally

The pages fetch `varieties.json` via `fetch()`, so they must be served over HTTP — opening `index.html` directly as a `file://` URL will not work.

```bash
python3 -m http.server 8000
# Then visit http://localhost:8000
```

No installation, no compilation.

## Architecture

The site is split across these files: [index.html](index.html) (markup), [styles.css](styles.css) (all styling), [main.js](main.js) (nav/menu/form behaviour), and [varieties.json](varieties.json) (all variety data).

- **HTML**: Multi-section SPA with smooth-scroll navigation (Hero → Varieties → About → Care Guide → Contact)
- **CSS**: Embedded `<style>` block using CSS custom properties for the color/typography design system. Responsive breakpoints at 900px and 560px.
## Adding a new variety

Add an entry to [varieties.json](varieties.json). Every page (`index.html`, `varieties.html`, `variety.html`) fetches it at runtime and renders cards dynamically — no HTML changes needed. Set `"image"` to a path like `"images/MyOrchid.jpg"` or `null` to fall back to the CSS gradient defined by `"fill"`.

## Architecture

- **JavaScript**: [main.js](main.js) handles four page-level behaviors:
  1. Nav background transition on scroll (transparent → opaque at 60px)
  2. Mobile hamburger menu (full-screen overlay, closes on link click or Escape)
  3. Scroll-triggered `.fade-up` animations via `IntersectionObserver`
  4. Contact form submission (client-side only — shows success state, no backend)

**Images**: [images/Queen.jpg](images/Queen.jpg) (hero) and [images/Farm.jpg](images/Farm.jpg) (about section).

**External dependencies**: Google Fonts CDN (Cormorant Garamond + DM Sans) and a Google Maps embed in the contact section.

## Deployment

Copy `index.html` and the `images/` directory to any static web host. No build artifacts to generate.
