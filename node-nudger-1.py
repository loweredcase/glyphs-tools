#MenuTitle: Node Nudger
# -*- coding: utf-8 -*-
__doc__="""
Creates a GUI where you can "nudge nodes" in a specific glyph or selection of glyphs.
"""

# --------------------------------------------------------------------
# Addition Projects - Last Update, Nov 21 2025
# --------------------------------------------------------------------
# Glyph Tools: Node Nudger
# --------------------------------------------------------------------
# This script uses Vanilla to create a small window where you can:
# → Nudge Nodes by x and y values with random and fixed options
# → Option to make the new glyph on a new layer or in a new glyph
# → Option to rename the layer or new glyph
# → Use a Reset button that calls undo (same as pressing ⌘Z once)
# --------------------------------------------------------------------


import GlyphsApp, random
from GlyphsApp import GSGlyph, GSLayer, GSOFFCURVE, GSCURVE
from vanilla import Window, TextBox, EditText, Button, CheckBox, PopUpButton, HorizontalLine
from datetime import datetime

Font = Glyphs.font
random.seed()  # OS-entropy seed for true-random runs


# ---------------- start your engines ----------------

def parseInt(s, fallback=0):
	try:
		return int(str(s).strip())
	except Exception:
		return fallback

def timestamp_str():
	return datetime.now().strftime("%H%M%S")

def duplicateLayer_withName(layer, name_if_any=None, tag="NodeNudge"):
	g = layer.parent
	newLayer = layer.copy()
	baseName = layer.name or ""
	label = (name_if_any.strip() if (name_if_any and name_if_any.strip())
	         else f"{tag}_{timestamp_str()}")
	newLayer.name = (f"{baseName} {label}".strip() if baseName else label)
	g.layers.append(newLayer)
	return newLayer

def findNextVersionedGlyphName(baseName):
	i = 1
	while True:
		candidate = f"{baseName}.{i:03d}"
		if Font.glyphs[candidate] is None:
			return candidate
		i += 1

def duplicateGlyph_withSuffix(glyph, suffix_text=None):
	baseName = glyph.name
	if suffix_text and suffix_text.strip():
		newName = f"{baseName}{suffix_text.strip()}"
		if Font.glyphs[newName] is not None:
			newName = findNextVersionedGlyphName(baseName)
	else:
		newName = findNextVersionedGlyphName(baseName)
	newGlyph = GSGlyph()
	newGlyph.name = newName
	Font.glyphs.append(newGlyph)
	return newGlyph

def masterLayerForId(glyph, masterId):
	try:
		L = glyph.layers[masterId]
		if L is not None:
			return L
	except Exception:
		pass
	L = GSLayer()
	L.associatedMasterId = masterId
	glyph.layers.append(L)
	return L

def copyShapesFromTo(srcLayer, dstLayer):
	# Clear shapes robustly
	try:
		dstLayer.shapes = []
	except Exception:
		while dstLayer.shapes:
			dstLayer.shapes.pop()
	for sh in srcLayer.shapes:
		dstLayer.shapes.append(sh.copy())
	dstLayer.width = srcLayer.width

def focusLayer(layer):
	"""Best-effort focus of a layer in the Edit view."""
	try:
		Font.selectedLayers = [layer]
	except Exception:
		pass
	try:
		gName = layer.parent.name
		tab = Font.currentTab
		if tab is None:
			Font.newTab(f"/{gName}")
		else:
			txt = tab.text or ""
			if f"/{gName}" not in txt:
				sep = "" if (not txt or txt.endswith(" ")) else " "
				tab.text = f"{txt}{sep}/{gName}"
		wc = Font.parent.windowController()
		wc.setActiveLayer_(layer)
	except Exception:
		try:
			Font.setCurrentLayer_(layer)
		except Exception:
			pass
	# Final redraw safety
	try:
		Glyphs.redraw()
		if Font.currentTab:
			Font.currentTab.redraw()
	except Exception:
		pass


# ---------------- make an interface ----------------

class NodeNudgerUI(object):
	def __init__(self):
		self.w = Window((440, 580), "Node Nudger")

		y = 12
		# CLUSTER 1: Mode & Axes
		self.w.modeLabel = TextBox((12, y, 120, 18), "Mode:", sizeStyle="small")
		# 0=Random, 1=Fixed
		self.w.mode = PopUpButton(
			(60, y, 160, 20),
			["Random", "Fixed"],
			sizeStyle="small",
			callback=self.updateEnableStates
		)
		y += 26

		self.w.axisX = CheckBox((12, y, 120, 20), "Nudge X", value=True, sizeStyle="small")
		self.w.axisY = CheckBox((132, y, 120, 20), "Nudge Y", value=True, sizeStyle="small")
		y += 24

		self.w.sep0 = HorizontalLine((12, y, -12, 1)); y += 14

		# CLUSTER 2: Random ranges vs Fixed amounts
		self.w.rangeTitle = TextBox((12, y, -12, 18), "Random Range (used in Random mode):", sizeStyle="small"); y += 20

		# X range
		self.w.xLabel = TextBox((12, y, 60, 18), "X:", sizeStyle="small")
		self.w.xMin = EditText((44, y, 60, 22), "", sizeStyle="small")
		self.w.xMax = EditText((110, y, 60, 22), "", sizeStyle="small")
		try:
			self.w.xMin._nsObject.setPlaceholderString_("min")
			self.w.xMax._nsObject.setPlaceholderString_("max")
		except Exception:
			pass

		# Y range
		self.w.yLabel = TextBox((190, y, 60, 18), "Y:", sizeStyle="small")
		self.w.yMin = EditText((214, y, 60, 22), "", sizeStyle="small")
		self.w.yMax = EditText((280, y, 60, 22), "", sizeStyle="small")
		try:
			self.w.yMin._nsObject.setPlaceholderString_("min")
			self.w.yMax._nsObject.setPlaceholderString_("max")
		except Exception:
			pass
		y += 30

		self.w.fixedTitle = TextBox((12, y, -12, 18), "Fixed Value (used in Fixed mode):", sizeStyle="small"); y += 20
		self.w.fxLabel = TextBox((12, y, 60, 18), "X:", sizeStyle="small")
		self.w.fixX  = EditText((44, y, 60, 22), "", sizeStyle="small")
		try:
			self.w.fixX._nsObject.setPlaceholderString_("e.g. 12")
		except Exception:
			pass
		self.w.fyLabel = TextBox((190, y, 60, 18), "Y:", sizeStyle="small")
		self.w.fixY  = EditText((214, y, 60, 22), "", sizeStyle="small")
		try:
			self.w.fixY._nsObject.setPlaceholderString_("e.g. -6")
		except Exception:
			pass
		y += 30

		self.w.sep1 = HorizontalLine((12, y, -12, 1)); y += 14

		# CLUSTER 2.5: Handle behavior
		self.w.preserve = CheckBox(
			(12, y, -12, 20),
			"Preserve curve shape (move handles with curve points)",
			value=True,
			sizeStyle="small"
		); y += 22
		self.w.nudgeHandles = CheckBox(
			(12, y, -12, 20),
			"Nudge points and handles independenly",
			value=False,
			sizeStyle="small"
		); y += 28

		self.w.sep2 = HorizontalLine((12, y, -12, 1)); y += 14

		# CLUSTER 3: Save options — New Layer (in-place)
		self.w.makeNewLayer = CheckBox(
			(12, y, -12, 20),
			"Create new layer before running (non-destructive).",
			value=False,
			sizeStyle="small",
			callback=self.updateEnableStates
		); y += 22
		self.w.layerNameLabel = TextBox((12, y, -12, 16), "New layer name (optional):", sizeStyle="small"); y += 18
		self.w.layerName = EditText((12, y, -12, 22), "", sizeStyle="small")
		try:
			self.w.layerName._nsObject.setPlaceholderString_("e.g. NodeNudge_123045")
		except Exception:
			pass
		y += 26

		self.w.openTab = CheckBox(
			(24, y, -12, 20),
			"Open new layer in a new Edit tab.",
			value=False,
			sizeStyle="small"
		); y += 30

		self.w.sep3 = HorizontalLine((12, y, -12, 1)); y += 14

		# CLUSTER 4: Save options — New Glyph
		self.w.makeNewGlyph = CheckBox(
			(12, y, -12, 20),
			"Draw to a new glyph.",
			value=False,
			sizeStyle="small",
			callback=self.updateEnableStates
		); y += 22
		self.w.glyphSuffixLabel = TextBox((12, y, -12, 16), "New glyph suffix (optional):", sizeStyle="small"); y += 18
		self.w.glyphSuffix = EditText((12, y, -12, 22), "", sizeStyle="small")
		try:
			self.w.glyphSuffix._nsObject.setPlaceholderString_(".alt  or  .ss01   (blank = auto .001)")
		except Exception:
			pass
		y += 32

		# Buttons: Run / Reset / Close
		self.w.runBtn   = Button((12,   y, 130, 32), "Run 🏁",   callback=self.run)
		self.w.resetBtn = Button((154,  y, 130, 32), "Reset ⌘Z", callback=self.reset)
		self.w.closeBtn = Button((296,  y, 130, 32), "Close",    callback=self.close)
		y += 44

		# Trim bottom
		x, yy, w, h = self.w.getPosSize()
		self.w.resize(w, y)

		self.updateEnableStates()
		self.w.open()

	# ---------- edit view updates ----------

	def updateEnableStates(self, sender=None):
		mode = self.w.mode.get()  # 0=random, 1=fixed
		# Enable random fields:
		self.w.xMin.enable(mode == 0)
		self.w.xMax.enable(mode == 0)
		self.w.yMin.enable(mode == 0)
		self.w.yMax.enable(mode == 0)
		# Enable fixed fields:
		self.w.fixX.enable(mode == 1)
		self.w.fixY.enable(mode == 1)
		# New layer/open-tab availability (disabled if New Glyph is on)
		allowLayerControls = bool(self.w.makeNewLayer.get()) and not bool(self.w.makeNewGlyph.get())
		self.w.layerName.enable(allowLayerControls)
		self.w.openTab.enable(allowLayerControls)

	# ---------------- oh shit undo ----------------

	def reset(self, sender):
		"""
		Reset button: calls the document's undo manager once,
		which should undo the last script operation (same as ⌘Z).
		"""
		global Font
		Font = Glyphs.font
		if not Font:
			return
		try:
			doc = Font.parent  # GSDocument
			if doc and hasattr(doc, "undoManager"):
				um = doc.undoManager()
				if um:
					um.undo()
			else:
				# Fallback: try glyph-level undo for selected layers
				for layer in (Font.selectedLayers or []):
					g = layer.parent
					if hasattr(g, "undoManager"):
						um = g.undoManager()
						if um:
							um.undo()
		except Exception as e:
			print(f"⚠️ Reset failed: {e}")
		# Redraw after undo
		try:
			if Font.currentTab:
				Font.currentTab.redraw()
			Glyphs.redraw()
		except Exception:
			pass

	# ---------------- the main event ----------------

	def run(self, sender):
		global Font
		Font = Glyphs.font  # refresh in case user switched fonts

		if not Font or not Font.selectedLayers:
			print("⚠️ Select one or more glyph layers first.")
			return

		mode = self.w.mode.get()  # 0=random range, 1=fixed amount
		affectX = bool(self.w.axisX.get())
		affectY = bool(self.w.axisY.get())
		if not (affectX or affectY):
			print("ℹ️ No-op: Neither X nor Y is selected.")
			return

		# random ranges (used in mode 0)
		xMin = parseInt(self.w.xMin.get(), 0)
		xMax = parseInt(self.w.xMax.get(), 0)
		yMin = parseInt(self.w.yMin.get(), 0)
		yMax = parseInt(self.w.yMax.get(), 0)
		if xMin > xMax: xMin, xMax = xMax, xMin
		if yMin > yMax: yMin, yMax = yMax, yMin

		# fixed amounts (used in mode 1)
		fixX = parseInt(self.w.fixX.get(), 0)
		fixY = parseInt(self.w.fixY.get(), 0)

		# handle behavior
		preserveCurves   = bool(self.w.preserve.get())
		nudgeOffCurves   = bool(self.w.nudgeHandles.get())

		# save options
		makeNewLayer = bool(self.w.makeNewLayer.get())
		newLayerName = self.w.layerName.get().strip() if makeNewLayer else ""
		openNewTab   = bool(self.w.openTab.get())
		makeNewGlyph = bool(self.w.makeNewGlyph.get())
		glyphSuffix  = self.w.glyphSuffix.get().strip() if makeNewGlyph else ""

		nudgedNodes = 0
		processedLayers = 0

		layersToFocus = []
		lastLayerToFocus = None

		Font.disableUpdateInterface()
		glyphsToUndo = set()
		try:
			# group by parent glyph
			byGlyph = {}
			for srcLayer in Font.selectedLayers:
				byGlyph.setdefault(srcLayer.parent, []).append(srcLayer)

			# decide target glyph per source glyph
			glyphMap = {}
			for srcGlyph, layers in byGlyph.items():
				tgtGlyph = duplicateGlyph_withSuffix(srcGlyph, glyphSuffix) if makeNewGlyph else srcGlyph
				glyphMap[srcGlyph] = tgtGlyph
				glyphsToUndo.add(tgtGlyph)

			# begin undo groups for all target glyphs
			for g in glyphsToUndo:
				try:
					g.beginUndo()
				except Exception:
					pass

			try:
				# build target layers
				layersToProcess = []
				for srcGlyph, srcLayers in byGlyph.items():
					tgtGlyph = glyphMap[srcGlyph]
					for srcLayer in srcLayers:
						masterId = getattr(srcLayer, "associatedMasterId", None)
						if not masterId:
							continue
						if makeNewGlyph:
							targetLayer = masterLayerForId(tgtGlyph, masterId)
							copyShapesFromTo(srcLayer, targetLayer)
							workingLayer = targetLayer
							lastLayerToFocus = workingLayer
						else:
							if makeNewLayer:
								workingLayer = duplicateLayer_withName(
									srcLayer,
									name_if_any=newLayerName,
									tag="NodeNudge"
								)
								layersToFocus.append(workingLayer)
							else:
								workingLayer = srcLayer
						layersToProcess.append(workingLayer)

				# nudge nodes
				for layer in layersToProcess:
					processedLayers += 1
					for path in layer.paths:
						nodes = path.nodes
						count = len(nodes)
						for i, node in enumerate(nodes):
							nodeType = node.type
							# determine dx, dy for this node
							dx = dy = 0
							if mode == 0:
								# random mode
								if affectX:
									dx = random.randint(xMin, xMax)
								if affectY:
									dy = random.randint(yMin, yMax)
							else:
								# fixed mode
								if affectX:
									dx = fixX
								if affectY:
									dy = fixY

							# skip if no movement
							if not (dx or dy):
								continue

							if nodeType == GSCURVE:
								# move the curve point
								node.x += dx
								node.y += dy
								nudgedNodes += 1

								# if preserving curve, also move adjacent handles (prev/next off-curve)
								if preserveCurves and count > 1:
									prevN = nodes[(i - 1) % count]
									nextN = nodes[(i + 1) % count]
									if prevN.type == GSOFFCURVE:
										prevN.x += dx
										prevN.y += dy
									if nextN.type == GSOFFCURVE:
										nextN.x += dx
										nextN.y += dy

							elif nodeType == GSOFFCURVE:
								# only move off-curve handles if explicitly allowed
								if nudgeOffCurves:
									node.x += dx
									node.y += dy
									nudgedNodes += 1

							else:
								# LINE or other on-curve types: just move the point
								node.x += dx
								node.y += dy
								nudgedNodes += 1

			finally:
				# end undo groups for all target glyphs
				for g in glyphsToUndo:
					try:
						g.endUndo()
					except Exception:
						pass

		finally:
			Font.enableUpdateInterface()

	# ---------- edit view updates ----------
	
		if makeNewGlyph:
			tab = Font.currentTab
			if tab is None:
				# No tab yet: show all *target* glyphs
				tabText = " ".join(f"/{glyphMap[src].name}" for src in byGlyph.keys())
				Font.newTab(tabText)
			else:
				txt = tab.text or ""
				if txt.strip():
					tokens = txt.split()
				else:
					tokens = []

				# for each source glyph, insert its new glyph token right after it
				for srcGlyph, tgtGlyph in glyphMap.items():
					if srcGlyph == tgtGlyph:
						continue  # not a duplicated glyph
					srcToken = f"/{srcGlyph.name}"
					tgtToken = f"/{tgtGlyph.name}"
					if tgtToken in tokens:
						continue  # already present

					inserted = False
					i = 0
					while i < len(tokens):
						if tokens[i] == srcToken:
							tokens.insert(i + 1, tgtToken)
							inserted = True
							i += 2
						else:
							i += 1

					if not inserted:
						# if we never saw the source token, append at the end
						tokens.append(tgtToken)

				tab.text = " ".join(tokens)

			if lastLayerToFocus is not None:
				focusLayer(lastLayerToFocus)

		elif layersToFocus:
			# no new glyph, but we may have new layers
			if openNewTab:
				Font.newTab([layersToFocus[-1]])
			else:
				focusLayer(layersToFocus[-1])

		# final redraw
		try:
			if Font.currentTab:
				Font.currentTab.redraw()
			Glyphs.redraw()
		except Exception:
			pass

		print(
			f"✔ Node Nudger: nudged {nudgedNodes} node(s) in {processedLayers} layer(s). "
			f"Mode={'Random' if mode==0 else 'Fixed'}, "
			f"AffectX={affectX}, AffectY={affectY}, "
			f"PreserveCurves={preserveCurves}, NudgeOffCurves={nudgeOffCurves}, "
			f"NewLayer={'YES' if (makeNewLayer and not makeNewGlyph) else 'NO'}, "
			f"NewGlyph={'YES' if makeNewGlyph else 'NO'}."
		)

	def close(self, sender):
		self.w.close()


NodeNudgerUI()
