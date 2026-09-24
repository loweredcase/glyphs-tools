# Addition Projects — Glyphs Tools

A small collection of modular drawing and font-production tools for **Glyphs 4**.

## Requirements

- Glyphs 4
- Python installed/selected in Glyphs
- Vanilla installed from **Window → Plugin Manager → Modules**

## Tools

### Drawing

- **Axis Twister** — adjust Smart Component / glyph-local axis values randomly or from fixed values, with component and axis scoping.
- **Component Swapper** — swap components from a pool, with targeting, modulo, chance, and non-destructive duplication options.
- **Node Nudger** — move on-curve nodes and/or handles by random or fixed X/Y values.
- **Rotator Jig** — build Intermediate layers across an axis to simulate rotational interpolation.
- **Seed Spreader** — propagate a parent/master drawing to related child layers.

### Production

- **Grid Snapper** — find component translations slightly off a chosen grid and snap them back into place.
- **Mirror Mender** — find reflected components and correct their transforms while preserving placement.
- **Vertical Metrics Maker** — calculate, preview, and apply vertical font metrics.

## Installation

### Plugin Manager

Once this collection is listed in the Glyphs package index, install it from:

**Window → Plugin Manager → Scripts**

Then hold **Option** and choose **Script → Reload Scripts**.

### Manual installation

1. In Glyphs, choose **Script → Open Scripts Folder**.
2. Put this repository (or an alias/symlink to it) in that folder.
3. Hold **Option** and choose **Script → Reload Scripts**.

The `Drawing` and `Production` folders appear as submenus in Glyphs’ Script menu.

## Development

The Git repository does not need to live inside the Glyphs Scripts folder. A convenient development setup is to keep one canonical checkout in a normal code folder and place an alias/symlink to it in the Glyphs 4 Scripts folder. VS Code edits the canonical checkout; Glyphs loads the same files through the alias/symlink.

## Glyphs 4 notes

This branch targets Glyphs 4’s current APIs, including glyph-local axes (`GSGlyph.axes`) for Smart Components and explicit Intermediate-layer coordinate APIs. Compatibility fallbacks are retained in a few places where they are harmless.

## License

Apache License 2.0. See `LICENSE`.

© Addition Projects 2026
