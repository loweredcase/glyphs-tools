## Overview

*A toolkit for modular, component-driven, and production workflows in Glyphs 4.*

  → **Axis Twister** adjusts Smart Component axes with random or targeted values  
  → **Component Swapper** swaps components from a defined replacement pool  
  → **Grid Snapper** finds and corrects components slightly off grid  
  → **Mirror Mender** finds and corrects mirrored components  
  → **Node Nudger** moves nodes by random or fixed X/Y values  
  → **Position Builder** generates positional OpenType behavior  
  → **Rotator Jig** builds Intermediate layers for faux-rotational effects  
  → **Seed Spreader** propagates a parent drawing across child layers  
  → **Streamer Builder** builds component-based positional glyph sets  
  → **Streamer Proofer** creates structured proofs for positional/contextual glyph systems  
  → **Vertical Metrics Maker** calculates and applies vertical font metrics  


**Requirements**  
  → Glyphs 4  
  → Python + Vanilla enabled  


**Installation**  
  → In Glyphs 4, open `Window → Plugin Manager`  
  → Under *Scripts*, find **AP Font Tools**  
  → Click *Install*  
  → Restart Glyphs or reload scripts if prompted  


**Manual / development installation**  
  → Clone or download this repo  
  → In Glyphs 4, open `Script → Open Scripts Folder`  
  → Place the repo in the Scripts folder  
  → Hold Option and choose `Script → Reload Scripts`  
  → For development, use the local repo instead of also installing through Plugin Manager to avoid duplicate scripts  


**Usage**  
  → Scripts appear under the *Script* menu after reloading  
  → Drawing and Production tools appear in their respective submenus  
  → Open `Window → Macro Panel` to inspect script output  

<br>

## Drawing Tools

**Axis Twister**  
*Adjust Smart Component axes in a glyph or selection of glyphs.*  
  → Use random ranges or fixed value lists  
  → Target all axes or a specific named axis  
  → Target all Smart Components or a defined component pool  
  → Control frequency with chance (%) and every-Nth settings  
  → Optional random counter generation  
  → Duplicate results to a new layer or glyph  
  → Reset with undo / ⌘Z  


**Component Swapper**  
*Swap targeted components from a defined replacement pool.*  
  → Swap randomly or cycle through replacements  
  → Target one component name or all components  
  → Apply even/odd or every-Nth alternation  
  → Control frequency with chance (%)  
  → Duplicate results to a new layer or glyph  
  → Reset with undo  


**Node Nudger**  
*Move nodes in a glyph or selection of glyphs.*  
  → Apply random or fixed X/Y movement  
  → Nudge X and Y independently  
  → Preserve curves by moving handles with on-curve points  
  → Or move handles independently for more disruptive results  
  → Duplicate results to a new layer or glyph  
  → Reset with undo  


**Rotator Jig**  
*Build Intermediate layers for faux-rotational effects.*  
  → Creates Intermediate layers along a chosen axis  
  → Rotates the current-master drawing around a fixed center  
  → Generates frames by degree step  
  → Supports clockwise or counter-clockwise rotation  
  → Optional integer rounding avoids fractional node coordinates  
  → Safe to rerun; only generated Intermediate layers are rebuilt  
  → Reset with undo / ⌘Z  

  **Rotation note:**  
  Rotator Jig stops one unit before the axis maximum—for example, `999` on a `0–1000` axis. For seamless loops, use the same drawing at both endpoint masters. This avoids interpolation artifacts at the axis seam and supports clean looping from start → rotation → start.  


**Seed Spreader**  
*Propagate a parent drawing across all child layers of a glyph.*  
  → Works across selected glyphs  
  → Optionally copies anchors and width  
  → Optionally skips child layers that already contain drawing  
  → Reset with undo / ⌘Z  

<br>

## Production Tools

**Grid Snapper**  
*Find components slightly off grid and snap them into place.*  
  → Scope by selected layers, selected glyphs, or all exportable glyphs  
  → Choose current or all masters  
  → Set grid increment and tolerance  
  → Preview changes before applying them  
  → Reset with undo / ⌘Z  


**Mirror Mender**  
*Find mirrored components and correct them without changing their visual placement.*  
  → Scope by selected layers, selected glyphs, or all exportable glyphs  
  → Choose current or all masters  
  → Preview changes before applying them  
  → Reset with undo / ⌘Z  


**Streamer Builder**  
*Build component-based isolated, initial, medial, and final forms for positional glyph systems.*  
  → Builds `.medi`, `.init`, `.fina`, and `.isol` forms from reusable start, middle, and end components  
  → Constructs medial forms from the default glyph with a background middle component  
  → Adds independent LSB / RSB space around the default glyph  
  → Optionally stretches the middle component to match each medial glyph width  
  → Calculates middle-component stretching independently for each master  
  → Suggests underscore-prefixed helper glyphs while allowing any valid component name  
  → Build from selected glyphs, all eligible glyphs, or a custom glyph list  
  → Customizable positional suffixes  
  → Preview source glyphs and construction before building  
  → Skip existing forms by default or explicitly rebuild them  
  → Preserves non-master special layers when rebuilding  


**Position Builder**  
*Generate positional OpenType behavior from matching alternate glyph sets.*  
  → Detects complete isolated / initial / medial / final sets  
  → Customizable suffixes and target OpenType feature  
  → Handles single glyphs and runs of 2, 3, 4+ glyphs  
  → Generates synchronized positional classes automatically  
  → Reports incomplete sets  
  → Safe to rerun as the font develops  
  → Preserves unrelated code in the target feature  


**Streamer Proofer**  
*Build structured proofs for positional and contextual glyph systems.*  
  → Detects complete isolated / initial / medial / final sets  
  → Proof literal forms or contextual OpenType behavior  
  → Customizable suffixes and feature tag  
  → Proof all complete sets or selected positional families  
  → Reports incomplete sets before proofing  


**Vertical Metrics Maker**  
*Calculate and apply vertical font metrics from drawing extremes and master settings.*  
  → Scans glyph outlines for vertical extremes  
  → Applies a recommended metric recipe for common export scenarios  
  → Writes font-level and master-level parameters where appropriate  
  → Optional line-gap calculation based on Ascender + Descender  
  → Preview values before applying them  
  → Safe to rerun; existing parameters are updated rather than duplicated  
  → Reset with undo / ⌘Z  


<br>
<br>

© Addition Projects 2026