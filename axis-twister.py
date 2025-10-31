#MenuTitle: Axis Twister
# -*- coding: utf-8 -*-
__doc__="""
Creates a GUI where you can "twist" Smart Component Axis in selected layers. Choose Random (each axis gets a random value in the given ranges) or Fixed (all axes get the same deltas). Optional: duplicate to a new layer or glyph first, with a custom name.
"""

# --------------------------------------------------------------------
# Addition Projects - Last Update, Oct 31 2025
# --------------------------------------------------------------------
# Axis Twister
# --------------------------------------------------------------------
# This script uses Vanilla to create a small window where you can:
# → Alter smart component axes values
# → Choose whether to change all axes or only one
# → Option to change randomly or fixed
# → Option to make the new Glyph on a new layer or in a new glyph
# --------------------------------------------------------------------


import GlyphsApp, random
from datetime import datetime
from vanilla import Window, TextBox, EditText, Button, PopUpButton, CheckBox

font = Glyphs.font
random.seed()

# ---------- helpers ----------

def ts_stamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def parse_int(s, fallback=0):
    try:
        return int(str(s).strip())
    except Exception:
        return fallback

def parse_float(s, fallback=0.0):
    try:
        return float(str(s).strip())
    except Exception:
        return fallback

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def parse_pool(text):
    return [n.strip() for n in text.split(",") if n.strip()]

def discover_axis_names_from_selection(layers):
    names = set()
    for layer in layers or []:
        for comp in layer.components:
            base = comp.component
            if not base or comp.smartComponentValues is None:
                continue
            axes = base.smartComponentAxes or []
            for ax in axes:
                if ax and ax.name:
                    names.add(ax.name)
    return sorted(names)

def axis_map_for_component(comp):
    """
    { axisName: (axisID, minVal, maxVal) } for this component
    """
    mapping = {}
    base = comp.component
    if not base or comp.smartComponentValues is None:
        return mapping
    axes = base.smartComponentAxes or []
    for ax in axes:
        if not ax:
            continue
        mapping[ax.name] = (ax.id, float(ax.bottomValue), float(ax.topValue))
    return mapping

def duplicate_layer(layer, name_hint="SmartAxis "+ts_stamp()):
    g = layer.parent
    new_layer = layer.copy()
    new_layer.name = name_hint
    g.layers.append(new_layer)
    return new_layer

def ensure_new_glyph_from_layer(layer, suffix=".001", open_in_tab=False):
    g = layer.parent
    base_name = g.name
    suf = suffix.strip()
    if not suf:
        idx = 1
        while font.glyphs[base_name + ".%03d" % idx] is not None:
            idx += 1
        suf = ".%03d" % idx
    new_name = base_name + suf

    new_glyph = font.glyphs[new_name]
    if new_glyph is None:
        new_glyph = GSGlyph(new_name)
        font.glyphs.append(new_glyph)

    master = font.selectedFontMaster
    target_layer = new_glyph.layers[master.id]
    target_layer.shapes = [s.copy() for s in layer.shapes]

    if open_in_tab and font.currentTab:
        try:
            font.currentTab.text += "/" + new_name
        except Exception:
            pass

    return new_glyph, target_layer

# ---------- GUI ----------

class SmartAxisTweaker(object):
    def __init__(self):
        self.w = Window((420, 408), "Smart Axis Tweaker")

        y = 12

        # POSSIBLE COMPONENTS
        self.w.poolTitle = TextBox((12, y, -12, 16), "POSSIBLE COMPONENTS", sizeStyle="small"); y += 18
        self.w.poolLabel = TextBox((12, y, 150, 18), "Possible components:", sizeStyle="small")
        self.w.pool = EditText((160, y, -12, 22), "_part.circle, _part.square, _part.triangle", sizeStyle="small"); y += 28

        self.w.targetLabel = TextBox((12, y, 150, 18), "Target scope:", sizeStyle="small")
        # Wider popup, left aligned
        self.w.target = PopUpButton((160, y, 220, 20), ["All (in selection)", "Only names in pool"], sizeStyle="small"); y += 26

        # hairline
        self.w.hr1 = TextBox((12, y, -12, 1), " ", sizeStyle="small"); y += 8

        # AXIS SELECTION & MODE
        self.w.axisTitle = TextBox((12, y, -12, 16), "AXIS SELECTION & MODE", sizeStyle="small"); y += 18

        # axis popup
        axis_items = ["All axes"] + discover_axis_names_from_selection(font.selectedLayers or [])
        self.w.axisLabel = TextBox((12, y, 150, 18), "Axis:", sizeStyle="small")
        self.w.axisPopup = PopUpButton((160, y, 160, 20), axis_items, sizeStyle="small")
        self.w.axisRefresh = Button((326, y-1, 82, 24), "Refresh", callback=self.refreshAxes); y += 28

        self.w.modeLabel = TextBox((12, y, 150, 18), "Mode:", sizeStyle="small")
        self.w.modePopup = PopUpButton((160, y, 160, 20), ["Random in range", "Fixed value"], sizeStyle="small"); y += 26

        self.w.fixedLabel = TextBox((12, y, 150, 18), "Fixed value:", sizeStyle="small")
        self.w.fixedValue = EditText((160, y, 80, 22), "", placeholder="e.g. 50", sizeStyle="small"); y += 28

        self.w.pctLabel = TextBox((12, y, 150, 18), "Chance % (0–100):", sizeStyle="small")
        self.w.pct = EditText((160, y, 60, 22), "100", sizeStyle="small"); y += 26

        self.w.modLabel = TextBox((12, y, 150, 18), "Every Nth component:", sizeStyle="small")
        self.w.modulo = EditText((160, y, 60, 22), "1", sizeStyle="small")
        self.w.modHint = TextBox((226, y, -12, 18), "1 = all, 2 = every other, 3 = every third…", sizeStyle="small"); y += 28

        # hairline
        self.w.hr2 = TextBox((12, y, -12, 1), " ", sizeStyle="small"); y += 8

        # SAVE OPTIONS
        self.w.saveTitle = TextBox((12, y, -12, 16), "SAVE OPTIONS", sizeStyle="small"); y += 18

        self.w.makeNewLayer = CheckBox((12, y, 200, 20), "Create new layer", value=False, sizeStyle="small")
        self.w.newLayerName = EditText((160, y, 140, 22), "", placeholder="timestamp if empty", sizeStyle="small")
        self.w.openLayerTab = CheckBox((306, y, -12, 20), "Open in tab", value=False, sizeStyle="small"); y += 26

        self.w.makeNewGlyph = CheckBox((12, y, 200, 20), "Create new glyph", value=False, sizeStyle="small")
        self.w.newGlyphSuffix = EditText((160, y, 140, 22), ".001", placeholder="e.g. .ss01 or .alt", sizeStyle="small")
        self.w.openGlyphTab = CheckBox((306, y, -12, 20), "Open in tab", value=False, sizeStyle="small"); y += 30

        # hairline
        self.w.hr3 = TextBox((12, y, -12, 1), " ", sizeStyle="small"); y += 8

        # Buttons (trim bottom margin to match your other tools)
        self.w.runBtn = Button((12, y, 180, 32), "Run 🏁", callback=self.run)
        self.w.closeBtn = Button((228, y, 180, 32), "Close", callback=lambda s: self.w.close())

        self.w.open()

    def refreshAxes(self, sender):
        items = ["All axes"] + discover_axis_names_from_selection(font.selectedLayers or [])
        self.w.axisPopup.setItems(items)

    # ----- core ops -----

    def layers_to_process(self):
        src_layers = list(font.selectedLayers or [])
        make_layer = bool(self.w.makeNewLayer.get())
        make_glyph = bool(self.w.makeNewGlyph.get())

        layers_out = []
        new_layers_to_select = []

        for src in src_layers:
            target = src

            if make_glyph:
                suffix = self.w.newGlyphSuffix.get().strip()
                open_tab_g = bool(self.w.openGlyphTab.get())
                _, target = ensure_new_glyph_from_layer(src, suffix=suffix if suffix else ".001", open_in_tab=open_tab_g)

            if make_layer:
                name_hint = self.w.newLayerName.get().strip() or ("SmartAxis " + ts_stamp())
                target = duplicate_layer(target, name_hint=name_hint)
                new_layers_to_select.append(target)

            layers_out.append(target)

        if new_layers_to_select:
            try:
                font.selectedLayers = new_layers_to_select
            except Exception:
                pass

        return layers_out

    def axis_targets(self, comp):
        axis_choice_idx = self.w.axisPopup.get()
        selected_name = self.w.axisPopup.getItems()[axis_choice_idx]
        amap = axis_map_for_component(comp)
        out = []
        if not amap:
            return out
        if selected_name == "All axes":
            for nm, (axid, lo, hi) in amap.items():
                out.append((nm, axid, lo, hi))
        else:
            if selected_name in amap:
                axid, lo, hi = amap[selected_name]
                out.append((selected_name, axid, lo, hi))
        return out

    def run(self, sender):
        if not font or not font.selectedLayers:
            print("⚠️ Select one or more glyph layers first.")
            return

        pool = parse_pool(self.w.pool.get())
        scope_is_pool = (self.w.target.get() == 1)
        mode = self.w.modePopup.get()  # 0=random, 1=fixed
        chance = clamp(parse_int(self.w.pct.get(), 100), 0, 100)
        modulo_n = max(1, parse_int(self.w.modulo.get(), 1))

        layers = self.layers_to_process()
        total_axes_set = 0
        touched_components = 0

        random.seed()
        font.disableUpdateInterface()
        try:
            for layer in layers:
                comp_idx = 0
                for comp in layer.components:
                    comp_idx += 1

                    # only smart components
                    vals = comp.smartComponentValues
                    if vals is None:
                        continue

                    # pool scope (if enabled)
                    if scope_is_pool and comp.componentName not in pool:
                        continue

                    # modulo
                    if (comp_idx % modulo_n) != 0:
                        continue

                    # chance
                    if random.random() > (chance / 100.0):
                        continue

                    # targets (per component)
                    targets = self.axis_targets(comp)
                    if not targets:
                        continue

                    # mutate the proxy dict (do NOT reassign the whole property)
                    for axisName, axisID, lo, hi in targets:
                        if mode == 0:
                            # random in range (inclusive)
                            lo_i = int(round(min(lo, hi)))
                            hi_i = int(round(max(lo, hi)))
                            v = random.randint(lo_i, hi_i)
                        else:
                            v = clamp(parse_float(self.w.fixedValue.get(), 0.0), lo, hi)

                        # IMPORTANT: mutate the proxy dict per key:
                        vals[axisID] = v
                        total_axes_set += 1

                    touched_components += 1

            if font.currentTab:
                font.currentTab.redraw()

        finally:
            font.enableUpdateInterface()

        print(f"✔ Smart Axis Tweaker: set {total_axes_set} axis value(s) on {touched_components} component(s). "
              f"Mode={'Random' if mode==0 else 'Fixed'}, Chance={chance}%, Modulo={modulo_n}, "
              f"NewLayer={'yes' if self.w.makeNewLayer.get() else 'no'}, NewGlyph={'yes' if self.w.makeNewGlyph.get() else 'no'}.")
        
SmartAxisTweaker()
