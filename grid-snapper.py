#MenuTitle: Grid Snapper
# -*- coding: utf-8 -*-
__doc__ = """
Rounds component placement (transform translation) to a user-defined grid increment.
"""

# --------------------------------------------------------------------
# Addition Projects - Last Update, Feb 5 2026
# --------------------------------------------------------------------
# Glyph Tools: Grid Snapper
# --------------------------------------------------------------------
# This script uses Vanilla to create a small window where you can:
# → Detect components placed “off-grid” (translation not aligned)
# → Round translation to nearest N units (e.g. 25)
# → Optional tolerance: only snap when within ±T units of a gridline
# → Preview what will change before writing
# → Use a Reset button that calls undo (same as pressing ⌘Z once)
# --------------------------------------------------------------------


import GlyphsApp
from vanilla import Window, TextBox, EditText, Button, PopUpButton, HorizontalLine, TextEditor

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

def parseFloat(s, fallback=0.0):
	try:
		return float(str(s).strip())
	except Exception:
		return fallback

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

def snap_value(v, step):
	if step <= 0:
		return v
	return round(v / step) * step

def snap_if_within(v, step, tol):
	"""
	Return (newV, changed, deltaToNearest)
	- If tol <= 0: always snap.
	- If tol > 0: only snap if within ±tol of nearest gridline.
	"""
	if step <= 0:
		return (v, False, 0.0)
	nearest = snap_value(v, step)
	delta = nearest - v
	if tol <= 0:
		return (nearest, abs(delta) > 1e-6, delta)
	return (nearest, abs(delta) <= tol and abs(delta) > 1e-6, delta)

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

class GridSnapperUI(object):
	def __init__(self):
		self.W = 520
		self.w = Window((self.W, 662), "Grid Snapper")

		y = 12

		# CLUSTER 1: Scope
		self.w.scopeTitle = TextBox((12, y, -12, 16), "SCOPE", sizeStyle="small"); y += 18

		self.w.scopeLabel = TextBox((12, y, 160, 18), "Scan:", sizeStyle="small")
		self.w.scope = PopUpButton(
			(172, y, -12, 20),
			["Selected layers", "Selected glyphs", "All exportable glyphs"],
			sizeStyle="small",
			callback=self.updateEnableStates
		)
		y += 26

		self.w.masterLabel = TextBox((12, y, 160, 18), "Masters:", sizeStyle="small")
		self.w.masterScope = PopUpButton((172, y, -12, 20), ["Current master", "All masters"], sizeStyle="small")
		y += 26

		self.w.sep1 = HorizontalLine((12, y, -12, 1)); y += 12

		# CLUSTER 2: Snapping
		self.w.snapTitle = TextBox((12, y, -12, 16), "SNAP", sizeStyle="small"); y += 18

		self.w.stepLabel = TextBox((12, y, 160, 18), "Round to nearest:", sizeStyle="small")
		self.w.step = EditText((172, y, 60, 22), "25", sizeStyle="small")
		self.w.stepHint = TextBox((238, y, -12, 18), "units (e.g. 25 for a 25-unit grid)", sizeStyle="small")
		y += 28

		self.w.tolLabel = TextBox((12, y, 160, 18), "Tolerance (±):", sizeStyle="small")
		self.w.tol = EditText((172, y, 60, 22), "0", sizeStyle="small")
		self.w.tolHint = TextBox((238, y, -12, 18), "0 = snap everything; >0 = only near gridlines", sizeStyle="small")
		y += 28

		self.w.sep2 = HorizontalLine((12, y, -12, 1)); y += 12

		# CLUSTER 3: Preview (Clear button)
		self.w.prevTitle = TextBox((12, y, -86, 16), "PREVIEW", sizeStyle="small")
		self.w.clearBtnTop = Button((self.W - 12 - 70, y - 2, 70, 20), "Clear", callback=self.clearPreview)
		y += 28

		self.w.preview = TextEditor((12, y, -12, 260), text="Click Preview to find off-grid components.")
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
		self.w.preview.set("Click Preview to find off-grid components.")

	def updateEnableStates(self, sender):
		# Masters dropdown only matters when scanning beyond selected layers
		self.w.masterScope.enable(self.w.scope.get() != 0)

	def _collect_layers(self):
		global Font
		Font = Glyphs.font
		if not Font:
			return None, "⚠️ No font open."

		scopeIdx = self.w.scope.get()        # 0 layers, 1 glyphs, 2 exportable
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

	def _scan(self, layers, step, tol):
		ops = []
		lines = []
		totalComps = 0
		eligible = 0

		for layer in layers:
			layerHits = []
			for comp in (layer.components or []):
				totalComps += 1
				s = get_transform_struct(comp)
				if not s:
					continue

				m11, m12, m21, m22, tX, tY = s

				newX, xChanged, dx = snap_if_within(tX, step, tol)
				newY, yChanged, dy = snap_if_within(tY, step, tol)

				if not (xChanged or yChanged):
					continue

				eligible += 1
				sNew = (m11, m12, m21, m22, newX, newY)
				ops.append((comp, sNew))

				name = (comp.componentName or (comp.component.name if comp.component else "<?>"))
				if xChanged and yChanged:
					layerHits.append(f"   - {name}  (tX {tX:.2f}→{newX:.0f}, tY {tY:.2f}→{newY:.0f})")
				elif xChanged:
					layerHits.append(f"   - {name}  (tX {tX:.2f}→{newX:.0f}, tY unchanged)")
				else:
					layerHits.append(f"   - {name}  (tX unchanged, tY {tY:.2f}→{newY:.0f})")

			if layerHits:
				lines.append(f"/{layer.parent.name} — layer: {layer.name or '(master)'}")
				lines.extend(layerHits)
				lines.append("")

		if not lines:
			lines = ["No components qualify for snapping (given step + tolerance)."]

		header = [
			f"Layers scanned: {len(layers)}",
			f"Components scanned: {totalComps}",
			f"Qualify to snap: {eligible}",
			f"Snap step: {step} | Tolerance: ±{tol}",
			""
		]
		return ("\n".join(header + lines), ops)

	def doPreview(self, sender):
		layers, err = self._collect_layers()
		if err:
			self.w.preview.set(err)
			print(err)
			return

		step = parseFloat(self.w.step.get(), 25.0)
		tol  = parseFloat(self.w.tol.get(), 0.0)
		if step <= 0:
			msg = "⚠️ Step must be > 0."
			self.w.preview.set(msg)
			print(msg)
			return
		if tol < 0:
			msg = "⚠️ Tolerance must be ≥ 0."
			self.w.preview.set(msg)
			print(msg)
			return

		text, _ops = self._scan(layers, step, tol)
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

		step = parseFloat(self.w.step.get(), 25.0)
		tol  = parseFloat(self.w.tol.get(), 0.0)
		if step <= 0:
			print("⚠️ Step must be > 0.")
			return
		if tol < 0:
			print("⚠️ Tolerance must be ≥ 0.")
			return

		text, ops = self._scan(layers, step, tol)
		self.w.preview.set(text)

		if not ops:
			print("ℹ️ Nothing to snap.")
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

		print("✔ Grid Snapper")
		print(f"→ Snapped {fixed} component(s) to nearest {step} (tolerance ±{tol}).")
		print("✅ Done.")

	def close(self, sender):
		self.w.close()


GridSnapperUI()
