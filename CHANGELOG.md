# Changelog

## Glyphs 4 migration — 2026-09-24

- Reorganized scripts into `Drawing` and `Production` groups.
- Removed legacy `-1` suffixes from Component Swapper and Node Nudger filenames.
- Updated Axis Twister for Glyphs 4 glyph-local Smart Component axes (`GSGlyph.axes`) while retaining a Glyphs 3 fallback.
- Updated Rotator Jig to use the Glyphs 4 Intermediate-layer coordinate API, with an older-API fallback.
- Switched preview background color access to `AppKit.NSColor` rather than relying on a GlyphsApp re-export.
- Hardened Component Swapper’s glyph lookup fallback.
- Added `.gitignore` for macOS, Python cache, and personal VS Code settings.
- Updated documentation for Glyphs 4 installation and Plugin Manager distribution.

### Testing status

All scripts parse and compile successfully under Python 3. They still require an in-app smoke test in Glyphs 4 because the Glyphs runtime and UI objects are not available outside the application.
