# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Static marketing website for **THT Orchid Farm** — a family-owned phalaenopsis orchid farm in Đơn Dương, Lâm Đồng, Vietnam. Zero dependencies, zero build steps.

## Running Locally

```bash
# Open directly in browser
open index.html

# Or serve via a local static server
python3 -m http.server 8000
# Then visit http://localhost:8000
```

No installation, no compilation.

## Architecture

The site is split across three files: [index.html](index.html) (markup), [styles.css](styles.css) (all styling), and [main.js](main.js) (all behaviour).

- **HTML**: Multi-section SPA with smooth-scroll navigation (Hero → Varieties → About → Care Guide → Contact)
- **CSS**: Embedded `<style>` block using CSS custom properties for the color/typography design system. Responsive breakpoints at 900px and 560px.
- **JavaScript**: Embedded `<script>` block with four behaviors:
  1. Nav background transition on scroll (transparent → opaque at 60px)
  2. Mobile hamburger menu (full-screen overlay, closes on link click or Escape)
  3. Scroll-triggered `.fade-up` animations via `IntersectionObserver`
  4. Contact form submission (client-side only — shows success state, no backend)

**Images**: [images/Queen.jpg](images/Queen.jpg) (hero) and [images/Farm.jpg](images/Farm.jpg) (about section).

**External dependencies**: Google Fonts CDN (Cormorant Garamond + DM Sans) and a Google Maps embed in the contact section.

## Deployment

Copy `index.html` and the `images/` directory to any static web host. No build artifacts to generate.
