#MenuTitle: Mirror Mender
# -*- coding: utf-8 -*-
__doc__ = """
Finds mirrored (reflected) components and corrects them.
"""

# --------------------------------------------------------------------
# Addition Projects - Last Update, Feb 5 2026
# --------------------------------------------------------------------
# Glyph Tools: Mirror Mender
# --------------------------------------------------------------------
# This script uses Vanilla to create a small window where you can:
# → Detect mirrored components
# → Remove reflection via X/Y flip
# → Preserve placement by matching bounds (Bottom-left or Center)
# → Preview what will change before writing
# → Use a Reset button that calls undo (same as pressing ⌘Z once)
# --------------------------------------------------------------------


import math
import GlyphsApp
from vanilla import Window, TextBox, Button, PopUpButton, HorizontalLine, TextEditor

Font = Glyphs.font


# ---------- start your engines ----------

def doc_undo_once(font):
	try:
		doc = font.parent
		if doc and hasattr(doc, "undoManager"):
			um = doc.undoManager()
			if um:
				um.undo()
	except Exception:
		pass

def begin_doc_undo_group(font):
	try:
		doc = font.parent
		if doc and hasattr(doc, "undoManager"):
			um = doc.undoManager()
			if um and hasattr(um, "beginUndoGrouping"):
				um.beginUndoGrouping()
				return um
	except Exception:
		pass
	return None

def end_doc_undo_group(um):
	try:
		if um and hasattr(um, "endUndoGrouping"):
			um.endUndoGrouping()
	except Exception:
		pass

def get_transform_struct(comp):
	"""
	Returns (m11, m12, m21, m22, tX, tY) as floats.
	"""
	try:
		t = comp.transform
		if isinstance(t, (tuple, list)) and len(t) >= 6:
			return (float(t[0]), float(t[1]), float(t[2]), float(t[3]), float(t[4]), float(t[5]))
	except Exception:
		pass

	try:
		t = comp.transformStruct()
		return (float(t.m11), float(t.m12), float(t.m21), float(t.m22), float(t.tX), float(t.tY))
	except Exception:
		pass

	try:
		t = comp.transform
		return (float(t.m11), float(t.m12), float(t.m21), float(t.m22), float(t.tX), float(t.tY))
	except Exception:
		pass

	return None

def set_transform_struct(comp, s):
	try:
		comp.transform = (s[0], s[1], s[2], s[3], s[4], s[5])
		return True
	except Exception:
		pass
	try:
		comp.setTransform_(s)
		return True
	except Exception:
		return False

def det_of(s):
	m11, m12, m21, m22, _, _ = s
	return (m11 * m22 - m12 * m21)

def is_reflected(comp):
	s = get_transform_struct(comp)
	if not s:
		return False
	return det_of(s) < 0

def layer_bounds_complete(layer):
	if layer is None:
		return None

	for attr in ("completeBounds", "completeBoundsIncludingTransforms", "boundsIncludingComponents"):
		try:
			obj = getattr(layer, attr, None)
			if obj is None:
				continue
			b = obj() if callable(obj) else obj
			if b and b.size and b.size.width and b.size.height:
				x0 = float(b.origin.x)
				y0 = float(b.origin.y)
				return (x0, y0, x0 + float(b.size.width), y0 + float(b.size.height))
		except Exception:
			pass

	try:
		b = layer.bounds
		if b and b.size and b.size.width and b.size.height:
			x0 = float(b.origin.x)
			y0 = float(b.origin.y)
			return (x0, y0, x0 + float(b.size.width), y0 + float(b.size.height))
	except Exception:
		pass

	return None

def apply_affine_to_point(x, y, s):
	m11, m12, m21, m22, tX, tY = s
	return (m11 * x + m21 * y + tX, m12 * x + m22 * y + tY)

def bbox_from_transformed_base_bounds(baseBBox, s):
	minX, minY, maxX, maxY = baseBBox
	pts = [(minX, minY), (minX, maxY), (maxX, minY), (maxX, maxY)]
	tx = []
	ty = []
	for (x, y) in pts:
		X, Y = apply_affine_to_point(x, y, s)
		tx.append(X)
		ty.append(Y)
	return (min(tx), min(ty), max(tx), max(ty))

def center_of(b):
	return ((b[0] + b[2]) * 0.5, (b[1] + b[3]) * 0.5)

def delta_to_match(beforeB, afterB, mode="bottomleft"):
	if mode == "center":
		c0 = center_of(beforeB)
		c1 = center_of(afterB)
		return (c0[0] - c1[0], c0[1] - c1[1])
	return (beforeB[0] - afterB[0], beforeB[1] - afterB[1])

def flipX_in_component_space(s):
	m11, m12, m21, m22, tX, tY = s
	return (-m11, -m12, m21, m22, tX, tY)

def flipY_in_component_space(s):
	m11, m12, m21, m22, tX, tY = s
	return (m11, m12, -m21, -m22, tX, tY)

def choose_best_fix(beforeB, baseB, s, prefer="auto", anchor="bottomleft"):
	cands = []

	sY = flipY_in_component_space(s)
	if det_of(sY) >= 0:
		afterY = bbox_from_transformed_base_bounds(baseB, sY)
		dxY, dyY = delta_to_match(beforeB, afterY, anchor)
		cands.append(("Y", sY, dxY, dyY, abs(dxY) + abs(dyY)))

	sX = flipX_in_component_space(s)
	if det_of(sX) >= 0:
		afterX = bbox_from_transformed_base_bounds(baseB, sX)
		dxX, dyX = delta_to_match(beforeB, afterX, anchor)
		cands.append(("X", sX, dxX, dyX, abs(dxX) + abs(dyX)))

	if not cands:
		return None

	if prefer == "vertical":
		for c in cands:
			if c[0] == "Y":
				return c
	if prefer == "horizontal":
		for c in cands:
			if c[0] == "X":
				return c

	return sorted(cands, key=lambda t: t[4])[0]

def base_bounds_for_component_glyph(comp, masterId):
	try:
		g = comp.component
		if not g:
			return None
		L = g.layers[masterId]
		if not L:
			return None
		return layer_bounds_complete(L)
	except Exception:
		return None

def selected_glyphs(font):
	out = []
	for L in (font.selectedLayers or []):
		try:
			if L and L.parent and L.parent not in out:
				out.append(L.parent)
		except Exception:
			continue
	return out

def exportable_glyphs(font):
	out = []
	for g in (font.glyphs or []):
		try:
			if g and g.export:
				out.append(g)
		except Exception:
			continue
	return out


# ---------- make some interfaces ----------

class MirrorMenderUI(object):
	def __init__(self):
		self.W = 520
		self.w = Window((self.W, 640), "Mirror Mender")

		y = 12

		# CLUSTER 1: Scope
		self.w.scopeTitle = TextBox((12, y, -12, 16), "SCOPE", sizeStyle="small"); y += 18

		self.w.scopeLabel = TextBox((12, y, 160, 18), "Scan:", sizeStyle="small")
		self.w.scope = PopUpButton((172, y, -12, 20), ["Selected layers", "Selected glyphs", "All exportable glyphs"], sizeStyle="small", callback=self.updateEnableStates)
		y += 26

		self.w.masterLabel = TextBox((12, y, 160, 18), "Masters:", sizeStyle="small")
		self.w.masterScope = PopUpButton((172, y, -12, 20), ["Current master", "All masters"], sizeStyle="small")
		y += 26

		self.w.sep1 = HorizontalLine((12, y, -12, 1)); y += 12

		# CLUSTER 2: Mender
		self.w.menderTitle = TextBox((12, y, -12, 16), "MENDER", sizeStyle="small"); y += 18

		self.w.methodLabel = TextBox((12, y, 160, 18), "Method:", sizeStyle="small")
		self.w.method = PopUpButton((172, y, -12, 20), ["Auto", "Only vertical", "Only horizontal"], sizeStyle="small")
		y += 26

		self.w.anchorLabel = TextBox((12, y, 160, 18), "Anchor:", sizeStyle="small")
		self.w.anchor = PopUpButton((172, y, -12, 20), ["Bottom-left", "Center"], sizeStyle="small")
		y += 26

		self.w.sep2 = HorizontalLine((12, y, -12, 1)); y += 12

		# CLUSTER 3: Preview (Clear button lives here now)
		self.w.prevTitle = TextBox((12, y, -86, 16), "PREVIEW", sizeStyle="small")
		self.w.clearBtnTop = Button((self.W - 12 - 70, y - 2, 70, 20), "Clear", callback=self.clearPreview)
		try:
			self.w.clearBtnTop._nsObject.setBezelStyle_(1)  # subtle style if available
		except Exception:
			pass
		y += 26

		self.w.preview = TextEditor((12, y, -12, 250), text="Click Preview to find mirrored components.")
		try:
			ns = self.w.preview.getNSTextView()
			ns.setEditable_(False)
			ns.setSelectable_(True)
			ns.setDrawsBackground_(True)
			ns.setBackgroundColor_(GlyphsApp.NSColor.whiteColor())
		except Exception:
			pass
		y += 270

		self.w.sep3 = HorizontalLine((12, y, -12, 1)); y += 12

		# Buttons (computed from window width so none clip)
		btnY = y
		gap = 8
		btnH = 32
		left = 12
		right = 12
		avail = self.W - left - right - (gap * 3)
		btnW = int(avail / 4)

		self.w.previewBtn = Button((left + (btnW + gap) * 0, btnY, btnW, btnH), "Preview", callback=self.doPreview)
		self.w.runBtn     = Button((left + (btnW + gap) * 1, btnY, btnW, btnH), "Run 🏁", callback=self.run)
		self.w.resetBtn   = Button((left + (btnW + gap) * 2, btnY, btnW, btnH), "Reset ⌘Z", callback=self.reset)
		self.w.closeBtn   = Button((left + (btnW + gap) * 3, btnY, btnW, btnH), "Close", callback=self.close)
		y += 44

		# Trim
		x, yy, w, h = self.w.getPosSize()
		self.w.resize(w, y)

		self.updateEnableStates(None)
		self.w.open()

	def clearPreview(self, sender):
		self.w.preview.set("Click Preview to find mirrored components.")

	def updateEnableStates(self, sender):
		# Masters dropdown only matters when scanning beyond selected layers
		self.w.masterScope.enable(self.w.scope.get() != 0)

	def _settings(self):
		methodIdx = self.w.method.get()
		if methodIdx == 1:
			prefer = "vertical"
		elif methodIdx == 2:
			prefer = "horizontal"
		else:
			prefer = "auto"

		anchor = "center" if (self.w.anchor.get() == 1) else "bottomleft"
		return prefer, anchor

	def _collect_layers(self):
		global Font
		Font = Glyphs.font
		if not Font:
			return None, "⚠️ No font open."

		scopeIdx = self.w.scope.get()  # 0 layers, 1 glyphs, 2 exportable
		masters = []
		masterMode = self.w.masterScope.get()  # 0 current, 1 all

		if scopeIdx == 0:
			layers = list(Font.selectedLayers or [])
			if not layers:
				return None, "⚠️ Select one or more layers first."
			return layers, None

		# scopes that expand to glyphs:
		if masterMode == 0:
			m = Font.selectedFontMaster
			masters = [m] if m else []
		else:
			masters = list(Font.masters or [])

		masters = [m for m in masters if m is not None]
		if not masters:
			return None, "⚠️ No masters found."

		if scopeIdx == 1:
			glyphs = selected_glyphs(Font)
			if not glyphs:
				return None, "⚠️ No selected glyphs found."
		else:
			glyphs = exportable_glyphs(Font)
			if not glyphs:
				return None, "⚠️ No exportable glyphs found."

		layers = []
		for g in glyphs:
			for m in masters:
				try:
					L = g.layers[m.id]
					if L:
						layers.append(L)
				except Exception:
					continue

		if not layers:
			return None, "⚠️ No layers found for the chosen scope."
		return layers, None

	def _scan(self, layers, prefer, anchor):
		ops = []
		lines = []
		totalComps = 0
		mirrored = 0

		for layer in layers:
			masterId = getattr(layer, "associatedMasterId", None) or (Font.selectedFontMaster.id if Font.selectedFontMaster else None)
			if not masterId:
				continue

			layerHits = []
			for comp in (layer.components or []):
				totalComps += 1
				if not is_reflected(comp):
					continue

				s = get_transform_struct(comp)
				if not s:
					continue

				baseB = base_bounds_for_component_glyph(comp, masterId)
				if not baseB:
					continue

				beforeB = bbox_from_transformed_base_bounds(baseB, s)
				pick = choose_best_fix(beforeB, baseB, s, prefer=prefer, anchor=anchor)
				if not pick:
					continue

				axisUsed, sFix, dx, dy, _score = pick
				m11, m12, m21, m22, tX, tY = sFix
				sNew = (m11, m12, m21, m22, tX + dx, tY + dy)

				if det_of(sNew) < 0:
					continue

				ops.append((comp, sNew))
				mirrored += 1
				name = (comp.componentName or (comp.component.name if comp.component else "<?>"))
				layerHits.append(f"   - {name}  (fix {axisUsed}, Δx={int(round(dx))}, Δy={int(round(dy))})")

			if layerHits:
				lines.append(f"/{layer.parent.name} — layer: {layer.name or '(master)'}")
				lines.extend(layerHits)
				lines.append("")

		if not lines:
			lines = ["No mirrored components found in the selection."]

		header = [
			f"Layers scanned: {len(layers)}",
			f"Components scanned: {totalComps}",
			f"Mirrored found: {mirrored}",
			""
		]
		return ("\n".join(header + lines), ops)

	def doPreview(self, sender):
		layers, err = self._collect_layers()
		if err:
			self.w.preview.set(err)
			print(err)
			return

		prefer, anchor = self._settings()
		text, _ops = self._scan(layers, prefer, anchor)
		self.w.preview.set(text)

	def reset(self, sender):
		global Font
		Font = Glyphs.font
		if not Font:
			return
		doc_undo_once(Font)
		try:
			if Font.currentTab:
				Font.currentTab.redraw()
			Glyphs.redraw()
		except Exception:
			pass

	def run(self, sender):
		layers, err = self._collect_layers()
		if err:
			print(err)
			return

		prefer, anchor = self._settings()
		text, ops = self._scan(layers, prefer, anchor)
		self.w.preview.set(text)

		if not ops:
			print("ℹ️ Nothing to fix.")
			return

		Font.disableUpdateInterface()
		um = begin_doc_undo_group(Font)
		try:
			fixed = 0
			for comp, sNew in ops:
				if set_transform_struct(comp, sNew):
					fixed += 1
		finally:
			end_doc_undo_group(um)
			Font.enableUpdateInterface()
			try:
				if Font.currentTab:
					Font.currentTab.redraw()
				Glyphs.redraw()
			except Exception:
				pass

		print("✔ Mirror Mender")
		print(f"→ Fixed {fixed} mirrored component(s).")
		print("✅ Done.")

	def close(self, sender):
		self.w.close()


MirrorMenderUI()
