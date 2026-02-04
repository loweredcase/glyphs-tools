## Overview  

A compact toolkit for modular and component-driven workflows in Glyphs 3:  
  → **Axis Twister** adjusts Smart Component axes (random or targeted); non-destructive options  
  → **Component Swapper** swaps components by pool, target scope, modulo; non-destructive options  
  → **Node Nudger** moves on-curve nodes by random or fixed x/y values; non-destructive options  
  → **Rotation Jig** builds Intermediate axis layers to simulate rotation via frame steps  
  → **Seed Spreader** helps propagates a parent drawing across all child layers of a glyph  
  → **Vertical Metrics Maker** calculate and apply vertical font metrics based on drawing extremes and master settings  


**Requirements**  
  → Glyphs 3 (3.4.x–3.5.x)  
  → Python + Vanilla enabled  


**Installation**  
  → Clone or download this repo  
  → Place scripts in your Glyphs Scripts folder:  
      `Glyphs → Preferences → Addons → Scripts → Open Scripts Folder`  
  → Refresh scripts:  
      `Scripts → Reload Scripts`  


**Usage**  
  → Scripts appear under the *Scripts* menu after reloading  
  → Open *Window → Macro Panel* to inspect output  


## Tools  

*Axis Twister*  
Creates a GUI where you can “twist” Smart Component Axes in a specific glyph or selection of glyphs.  
  → Random ranges (min/max per axis, clamped to axis limits)  
  → Fixed lists (e.g. `100, 50, 25`) randomly applied per component  
  → Axis scoping: all axes or a specific named axis  
  → Component scoping: all smart components or only names in a pool  
  → Chance (%) + affect every Nth component (`1 = all`, `2 = every other`, `3 = every third`)  
  → Optional random counter generation (decompose + reverse shapes to create cutouts)  
  → Duplicate to new layer or new glyph with custom naming  
  → New glyphs appear immediately after the original in the Edit tab  
  → Reset button (`undo / ⌘Z`)  


*Component Swapper*  
Creates a GUI where you can control swapping components in a specific glyph or selection of glyphs.  
  → Define a pool of replacement components  
  → Swap randomly from the pool  
  → Or swap using a specific list (`A → B → C → …`)  
  → Target scope: all components in the pool or a single component name  
  → Modulo alternation: even/odd or every Nth component  
  → Chance (%) determines how often replacements occur  
  → Duplicate to new layer or new glyph with a suffix or versioning  
  → Edit-tab updates insert new glyphs directly after the original  
  → Reset button (`undo`)  


*Node Nudger*  
Creates a GUI where you can "nudge nodes" in a specific glyph or selection of glyphs.  
  → Random or fixed X/Y nudging  
  → Independent toggles for “Nudge X” and “Nudge Y”  
  → Preserve-curve mode (move handles with on-curve points)  
  → Or nudge handles independently (for more glitch-driven outcomes)  
  → Duplicate to new layer or new glyph (timestamped naming options)  
  → New glyphs appear directly after the source in the Edit tab  
  → Reset button (`undo`)  


*Rotator Jig*  
Creates a GUI to automate "rotational" intermediate layers.  
  → Builds real Intermediate (brace) layers along a chosen axis (current master only)  
  → Copies current-master outlines into each brace layer and rotates geometry around a fixed center  
  → Generates frames by degree step (endpoints excluded)  
  → Clockwise / counter-clockwise direction toggle  
  → Optional integer rounding to avoid fractional node coordinates  
  → Safe to rerun (rebuilds only the generated brace layers)  
  → Reset button (`undo / ⌘Z`)  

  *Note on rotation*  
  → Rotator Jig intentionally caps its final intermediate brace at **max-1** (e.g. **999** when max is 1000)  
  → This avoids interpolation artifacts at endpoints, due to for example a start node changing positions through rotation, and supports clean looping for animation (1 → 999 → 1)  


*Seed Spreader*  
Create a GUI that helps propagates a parent drawing across all child layers of a glyph, enabling fast expansion of component-based character sets across multiple axes and styles  
  → Propagate parent drawing to all child layers for selected glyph(s)  
  → Optionally copy anchors + width  
  → Optionally skip child layers that already contain drawing  
  → Run in undo groups + Reset (⌘Z)  


*Vertical Metrics Maker*  
Create a GUI and helper to calculate and apply vertical font metrics based on drawing extremes and master settings. Designed to support consistent vertical behavior across masters and exports.  
→ Scans glyph outlines to determine vertical extremes  
→ Applies a recommended metric recipe for common export scenarios  
→ Writes font-level and master-level custom parameters correctly  
→ Optional line-gap calculation as a percentage of Ascender + Descender  
→ Preview computed values before writing  
→ Safe to rerun; existing parameters are updated, not duplicated  
→ Reset button (single undo / ⌘Z)  

  

© Addition Projects 2026
